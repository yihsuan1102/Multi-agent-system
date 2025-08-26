"""
API 3, 4, 5 測試
測試會話相關 API 的各種情境，包含錯誤處理
"""
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from maiagent.chat.models import Group, GroupScenarioAccess, Message, Scenario, Session
from maiagent.chat.tests.factories import (
    GroupFactory,
    MessageFactory,
    ScenarioFactory,
    SessionFactory,
    UserFactory,
)
from maiagent.users.models import User

User = get_user_model()


class SessionListAPITestCase(APITestCase):
    """API 3: 顯示所有會話測試案例"""
    
    def setUp(self):
        """測試前準備"""
        # 建立測試群組
        self.group = GroupFactory()
        
        # 建立測試使用者
        self.user = UserFactory(group=self.group)
        
        # 建立測試場景
        self.scenario = ScenarioFactory()
        
        # 建立群組場景存取權
        GroupScenarioAccess.objects.create(
            group=self.group,
            scenario=self.scenario
        )
        
        # 建立測試會話
        self.session1 = SessionFactory(
            user=self.user,
            scenario=self.scenario,
            status=Session.Status.ACTIVE
        )
        self.session2 = SessionFactory(
            user=self.user,
            scenario=self.scenario,
            status=Session.Status.CLOSED
        )
        
        # 取得 JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # 設定認證標頭
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_list_sessions_success(self):
        """測試成功取得會話列表"""
        url = reverse('api:conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('conversations', response_data['data'])
        self.assertIn('filters', response_data['data'])
        self.assertEqual(response_data['message'], '會話列表取得成功')
        self.assertIn('timestamp', response_data)
    
    def test_list_sessions_with_status_filter(self):
        """測試使用狀態篩選"""
        url = reverse('api:conversation-list')
        response = self.client.get(url, {'status': 'Active'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # 應該只有一個 Active 狀態的會話
        conversations = response_data['data']['conversations']
        self.assertEqual(len(conversations), 1)
    
    def test_list_sessions_with_scenario_filter(self):
        """測試使用場景篩選"""
        url = reverse('api:conversation-list')
        response = self.client.get(url, {'scenario_id': str(self.scenario.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # 應該有兩個會話
        conversations = response_data['data']['conversations']
        self.assertEqual(len(conversations), 2)
    
    def test_list_sessions_invalid_status_parameter(self):
        """測試無效的狀態參數"""
        url = reverse('api:conversation-list')
        response = self.client.get(url, {'status': 'InvalidStatus'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)
    
    def test_list_sessions_invalid_page_parameter(self):
        """測試無效的頁數參數"""
        url = reverse('api:conversation-list')
        response = self.client.get(url, {'page': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)
    
    def test_list_sessions_invalid_scenario_id(self):
        """測試無效的場景 ID"""
        url = reverse('api:conversation-list')
        response = self.client.get(url, {'scenario_id': 'invalid-uuid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)
    
    def test_list_sessions_without_authentication(self):
        """測試未認證的請求"""
        # 移除認證標頭
        self.client.credentials()
        
        url = reverse('api:conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_sessions_user_without_group(self):
        """測試沒有群組的使用者"""
        # 建立沒有群組的使用者
        user_without_group = UserFactory(group=None)
        refresh = RefreshToken.for_user(user_without_group)
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        url = reverse('api:conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response_data = response.json()
        self.assertEqual(response_data['detail'], '使用者 Role 沒有查看會話的權限')


class SessionRetrieveAPITestCase(APITestCase):
    """API 4: 查詢特定會話測試案例"""
    
    def setUp(self):
        """測試前準備"""
        self.group = GroupFactory()
        self.user = UserFactory(group=self.group)
        self.scenario = ScenarioFactory()
        
        # 建立群組場景存取權
        GroupScenarioAccess.objects.create(
            group=self.group,
            scenario=self.scenario
        )
        
        # 建立測試會話和訊息
        self.session = SessionFactory(
            user=self.user,
            scenario=self.scenario,
            status=Session.Status.ACTIVE
        )
        
        # 建立一些測試訊息
        self.message1 = MessageFactory(
            session=self.session,
            role=Message.Role.USER,
            content="第一條訊息"
        )
        self.message2 = MessageFactory(
            session=self.session,
            role=Message.Role.ASSISTANT,
            content="第二條訊息"
        )
        
        # 設定認證
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_retrieve_session_success(self):
        """測試成功取得會話詳情"""
        url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('session', response_data['data'])
        self.assertEqual(response_data['message'], '會話詳情取得成功')
        self.assertIn('timestamp', response_data)
    
    def test_retrieve_session_with_messages_pagination(self):
        """測試包含訊息分頁的會話詳情"""
        url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
        response = self.client.get(url, {
            'include_messages': 'true',
            'message_limit': 1,
            'message_offset': 0
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertIn('message_pagination', response_data['data'])
        pagination = response_data['data']['message_pagination']
        self.assertEqual(pagination['limit'], 1)
        self.assertEqual(pagination['offset'], 0)
        self.assertTrue(pagination['has_more'])
    
    def test_retrieve_session_exclude_messages(self):
        """測試不包含訊息的會話詳情"""
        url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
        response = self.client.get(url, {'include_messages': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertNotIn('message_pagination', response_data['data'])
    
    def test_retrieve_nonexistent_session(self):
        """測試查詢不存在的會話"""
        fake_session_id = str(uuid.uuid4())
        url = reverse('api:conversation-detail', kwargs={'pk': fake_session_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response_data = response.json()
        self.assertEqual(response_data['detail'], '會話不存在')
    
    def test_retrieve_session_invalid_message_limit(self):
        """測試無效的訊息限制參數"""
        url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
        response = self.client.get(url, {'message_limit': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)
    
    def test_retrieve_session_invalid_include_messages(self):
        """測試無效的 include_messages 參數"""
        url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
        response = self.client.get(url, {'include_messages': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)
    
    def test_retrieve_session_no_permission(self):
        """測試無權限查看會話"""
        # 建立另一個群組的使用者
        other_group = GroupFactory()
        other_user = UserFactory(group=other_group)
        
        refresh = RefreshToken.for_user(other_user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response_data = response.json()
        self.assertEqual(response_data['detail'], '使用者 Role 沒有查看該會話的權限')


class SessionDeleteAPITestCase(APITestCase):
    """API 5: 刪除特定對話測試案例"""
    
    def setUp(self):
        """測試前準備"""
        self.group = GroupFactory()
        self.user = UserFactory(group=self.group)
        self.scenario = ScenarioFactory()
        
        # 建立群組場景存取權
        GroupScenarioAccess.objects.create(
            group=self.group,
            scenario=self.scenario
        )
        
        # 建立測試會話和訊息
        self.session = SessionFactory(
            user=self.user,
            scenario=self.scenario,
            status=Session.Status.CLOSED
        )
        
        # 建立一些測試訊息
        MessageFactory(
            session=self.session,
            role=Message.Role.USER,
            content="測試訊息1"
        )
        MessageFactory(
            session=self.session,
            role=Message.Role.ASSISTANT,
            content="測試訊息2"
        )
        
        # 設定認證
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_delete_session_success(self):
        """測試成功刪除會話"""
        url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)
        self.assertEqual(response_data['data']['deleted_session_id'], str(self.session.id))
        self.assertEqual(response_data['data']['deleted_messages_count'], 2)
        self.assertIn('deletion_timestamp', response_data['data'])
        self.assertEqual(response_data['message'], '會話刪除成功')
        
        # 驗證會話已被刪除
        self.assertFalse(Session.objects.filter(id=self.session.id).exists())
    
    def test_delete_nonexistent_session(self):
        """測試刪除不存在的會話"""
        fake_session_id = str(uuid.uuid4())
        url = reverse('api:conversation-detail', kwargs={'pk': fake_session_id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response_data = response.json()
        self.assertEqual(response_data['detail'], '會話不存在')
    
    def test_delete_session_no_permission(self):
        """測試無權限刪除會話"""
        # 建立另一個群組的使用者
        other_group = GroupFactory()
        other_user = UserFactory(group=other_group)
        
        refresh = RefreshToken.for_user(other_user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response_data = response.json()
        self.assertEqual(response_data['detail'], '使用者沒有刪除該會話的權限')
    
    def test_delete_session_without_authentication(self):
        """測試未認證的刪除請求"""
        # 移除認證標頭
        self.client.credentials()
        
        url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('maiagent.chat.api.views.Session.delete')
    def test_delete_session_database_error(self):
        """測試資料庫錯誤"""
        # 模擬資料庫錯誤
        with patch('maiagent.chat.api.views.Session.delete') as mock_delete:
            mock_delete.side_effect = Exception("Database connection failed")
            
            url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
            response = self.client.delete(url)
            
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            response_data = response.json()
            self.assertEqual(response_data['detail'], '資料庫服務超載或系統維護中')


class SessionAPIIntegrationTestCase(APITestCase):
    """會話 API 整合測試"""
    
    def setUp(self):
        """測試前準備"""
        self.group = GroupFactory()
        self.user = UserFactory(group=self.group)
        self.scenario = ScenarioFactory()
        
        # 建立群組場景存取權
        GroupScenarioAccess.objects.create(
            group=self.group,
            scenario=self.scenario
        )
        
        # 設定認證
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_complete_session_lifecycle(self):
        """測試完整的會話生命週期"""
        # 1. 建立會話和訊息（通過 API 1）
        message_url = reverse('api:conversation-post-message-no-session')
        with patch('maiagent.chat.tasks.process_message.delay') as mock_delay:
            response = self.client.post(message_url, {
                'content': '測試會話',
                'scenario_id': str(self.scenario.id)
            }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session_id = response.json()['session_id']
        
        # 2. 查看會話列表（API 3）
        list_url = reverse('api:conversation-list')
        response = self.client.get(list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conversations = response.json()['data']['conversations']
        self.assertTrue(len(conversations) >= 1)
        
        # 3. 查詢特定會話詳情（API 4）
        detail_url = reverse('api:conversation-detail', kwargs={'pk': session_id})
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session_data = response.json()['data']['session']
        self.assertEqual(session_data['id'], session_id)
        
        # 4. 刪除會話（API 5）
        response = self.client.delete(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['deleted_session_id'], session_id)
        
        # 5. 驗證會話已被刪除
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)