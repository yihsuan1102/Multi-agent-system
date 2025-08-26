"""
核心 API 功能測試
測試 API 3, 4, 5 的基本讀/寫/刪除功能以及錯誤處理
"""
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rolepermissions.roles import assign_role

from maiagent.chat.models import Group, GroupScenarioAccess, Message, Scenario, Session
from maiagent.users.roles import Employee
from maiagent.chat.tests.factories import (
    GroupFactory,
    MessageFactory,
    ScenarioFactory,
    SessionFactory,
    UserFactory,
)

User = get_user_model()


class CoreAPIFunctionalityTestCase(APITestCase):
    """核心 API 功能測試"""
    
    def setUp(self):
        """測試前準備"""
        # 建立測試群組
        self.group = GroupFactory()
        
        # 建立測試使用者
        self.user = UserFactory(group=self.group, role='employee')
        # 為用戶分配角色權限
        assign_role(self.user, 'employee')
        
        # 建立測試場景
        self.scenario = ScenarioFactory()
        
        # 建立群組場景存取權
        GroupScenarioAccess.objects.create(
            group=self.group,
            scenario=self.scenario
        )
        
        # 建立測試會話
        self.session = SessionFactory(
            user=self.user,
            scenario=self.scenario,
            status=Session.Status.ACTIVE
        )
        
        # 建立測試訊息
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

    def test_api3_list_conversations_success(self):
        """測試 API 3: 成功列出會話"""
        url = reverse('api:conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('conversations', data['data'])
        self.assertIn('filters', data['data'])
        self.assertEqual(data['message'], '會話列表取得成功')
        
        # 驗證會話資料結構
        conversations = data['data']['conversations']
        self.assertTrue(len(conversations) >= 1)
        
        conversation = conversations[0]
        self.assertIn('id', conversation)
        self.assertIn('title', conversation)
        self.assertIn('user', conversation)
        self.assertIn('scenario', conversation)
        self.assertIn('status', conversation)
        self.assertIn('message_count', conversation)

    def test_api4_retrieve_conversation_success(self):
        """測試 API 4: 成功取得會話詳情"""
        url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('session', data['data'])
        self.assertEqual(data['message'], '會話詳情取得成功')
        
        # 驗證會話詳情結構
        session_data = data['data']['session']
        self.assertEqual(session_data['id'], str(self.session.id))
        self.assertIn('user', session_data)
        self.assertIn('scenario', session_data)
        self.assertIn('messages', session_data)
        
        # 驗證訊息資料
        messages = session_data['messages']
        self.assertEqual(len(messages), 2)

    def test_api5_delete_conversation_success(self):
        """測試 API 5: 成功刪除會話"""
        # 先確認會話存在
        self.assertTrue(Session.objects.filter(id=self.session.id).exists())
        
        url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], '會話刪除成功')
        
        # 驗證刪除詳情
        delete_data = data['data']
        self.assertEqual(delete_data['deleted_session_id'], str(self.session.id))
        self.assertEqual(delete_data['deleted_messages_count'], 2)
        self.assertIn('deletion_timestamp', delete_data)
        
        # 驗證會話已被刪除
        self.assertFalse(Session.objects.filter(id=self.session.id).exists())

    def test_database_read_operations(self):
        """測試資料庫讀取操作"""
        # 測試 API 3 - 讀取會話列表
        url = reverse('api:conversation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 測試 API 4 - 讀取特定會話
        url = reverse('api:conversation-detail', kwargs={'pk': str(self.session.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 驗證能正確讀取關聯資料
        data = response.json()
        session_data = data['data']['session']
        
        # 驗證用戶資料
        self.assertEqual(session_data['user']['username'], self.user.username)
        
        # 驗證場景資料
        self.assertEqual(session_data['scenario']['name'], self.scenario.name)
        
        # 驗證訊息資料
        messages = session_data['messages']
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['content'], "第一條訊息")
        self.assertEqual(messages[1]['content'], "第二條訊息")

    def test_database_write_operations(self):
        """測試資料庫寫入操作 (透過 API 1)"""
        # 測試建立新會話和訊息
        url = reverse('api:conversation-post-message-no-session')
        data = {
            'content': '測試新會話訊息',
            'scenario_id': str(self.scenario.id)
        }
        
        with patch('maiagent.chat.tasks.process_message.delay') as mock_delay:
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        response_data = response.json()
        new_session_id = response_data['session_id']
        
        # 驗證新會話已寫入資料庫
        new_session = Session.objects.get(id=new_session_id)
        self.assertEqual(new_session.user, self.user)
        self.assertEqual(new_session.scenario, self.scenario)
        
        # 驗證新訊息已寫入資料庫
        new_message = Message.objects.get(id=response_data['message']['id'])
        self.assertEqual(new_message.content, '測試新會話訊息')
        self.assertEqual(new_message.session, new_session)

    def test_database_delete_operations(self):
        """測試資料庫刪除操作"""
        # 建立要刪除的會話和訊息
        test_session = SessionFactory(
            user=self.user,
            scenario=self.scenario,
            status=Session.Status.CLOSED
        )
        test_message = MessageFactory(
            session=test_session,
            content="要被刪除的訊息"
        )
        
        # 確認資料存在
        self.assertTrue(Session.objects.filter(id=test_session.id).exists())
        self.assertTrue(Message.objects.filter(id=test_message.id).exists())
        
        # 執行刪除
        url = reverse('api:conversation-detail', kwargs={'pk': str(test_session.id)})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 驗證會話和相關訊息都已刪除
        self.assertFalse(Session.objects.filter(id=test_session.id).exists())
        self.assertFalse(Message.objects.filter(id=test_message.id).exists())


class CoreAPIErrorHandlingTestCase(APITestCase):
    """核心 API 錯誤處理測試"""
    
    def setUp(self):
        """測試前準備"""
        self.group = GroupFactory()
        self.user = UserFactory(group=self.group, role='employee')
        # 為用戶分配角色權限
        assign_role(self.user, 'employee')
        self.scenario = ScenarioFactory()
        
        # 設定認證
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_api3_error_400_invalid_parameters(self):
        """測試 API 3: 400 錯誤 - 無效參數"""
        url = reverse('api:conversation-list')
        response = self.client.get(url, {'page': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('detail', data)

    def test_api3_error_401_unauthorized(self):
        """測試 API 3: 401 錯誤 - 未認證"""
        self.client.credentials()  # 移除認證
        
        url = reverse('api:conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api3_error_403_no_group(self):
        """測試 API 3: 403 錯誤 - 無群組權限"""
        # 建立沒有群組的使用者
        user_without_group = UserFactory(group=None)
        refresh = RefreshToken.for_user(user_without_group)
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        url = reverse('api:conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        self.assertEqual(data['detail'], '使用者 Role 沒有查看會話的權限')

    def test_api4_error_404_session_not_found(self):
        """測試 API 4: 404 錯誤 - 會話不存在"""
        fake_session_id = str(uuid.uuid4())
        url = reverse('api:conversation-detail', kwargs={'pk': fake_session_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        self.assertEqual(data['detail'], '會話不存在')

    def test_api4_error_400_invalid_message_limit(self):
        """測試 API 4: 400 錯誤 - 無效訊息限制"""
        # 建立測試會話
        session = SessionFactory(user=self.user, scenario=self.scenario)
        GroupScenarioAccess.objects.create(group=self.group, scenario=self.scenario)
        
        url = reverse('api:conversation-detail', kwargs={'pk': str(session.id)})
        response = self.client.get(url, {'message_limit': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('detail', data)

    def test_api5_error_404_delete_nonexistent_session(self):
        """測試 API 5: 404 錯誤 - 刪除不存在的會話"""
        fake_session_id = str(uuid.uuid4())
        url = reverse('api:conversation-detail', kwargs={'pk': fake_session_id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        self.assertEqual(data['detail'], '會話不存在')

    def test_api5_error_403_no_delete_permission(self):
        """測試 API 5: 403 錯誤 - 無刪除權限"""
        # 建立另一個群組的會話
        other_group = GroupFactory()
        other_user = UserFactory(group=other_group)
        other_session = SessionFactory(user=other_user, scenario=self.scenario)
        
        url = reverse('api:conversation-detail', kwargs={'pk': str(other_session.id)})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        self.assertEqual(data['detail'], '使用者沒有刪除該會話的權限')


class DatabaseIntegrityTestCase(APITestCase):
    """資料庫完整性測試"""
    
    def setUp(self):
        """測試前準備"""
        self.group = GroupFactory()
        self.user = UserFactory(group=self.group, role='employee')
        # 為用戶分配角色權限
        assign_role(self.user, 'employee')
        self.scenario = ScenarioFactory()
        
        GroupScenarioAccess.objects.create(
            group=self.group,
            scenario=self.scenario
        )
        
        # 設定認證
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_cascade_delete_integrity(self):
        """測試級聯刪除的完整性"""
        # 建立會話和多個訊息
        session = SessionFactory(user=self.user, scenario=self.scenario)
        
        messages = []
        for i in range(5):
            message = MessageFactory(
                session=session,
                content=f"測試訊息 {i+1}"
            )
            messages.append(message)
        
        # 確認所有資料都存在
        self.assertTrue(Session.objects.filter(id=session.id).exists())
        self.assertEqual(Message.objects.filter(session=session).count(), 5)
        
        # 刪除會話
        url = reverse('api:conversation-detail', kwargs={'pk': str(session.id)})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 驗證會話和所有相關訊息都已刪除
        self.assertFalse(Session.objects.filter(id=session.id).exists())
        self.assertEqual(Message.objects.filter(session_id=session.id).count(), 0)
        
        # 驗證刪除回應中的訊息數量正確
        data = response.json()
        self.assertEqual(data['data']['deleted_messages_count'], 5)

    def test_data_model_relationships(self):
        """測試資料模型關聯性"""
        # 建立完整的資料結構
        session = SessionFactory(user=self.user, scenario=self.scenario)
        message = MessageFactory(session=session)
        
        # 透過 API 4 測試關聯資料的正確讀取
        url = reverse('api:conversation-detail', kwargs={'pk': str(session.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        session_data = data['data']['session']
        
        # 驗證用戶關聯
        self.assertEqual(session_data['user']['id'], str(self.user.id))
        self.assertEqual(session_data['user']['username'], self.user.username)
        
        # 驗證場景關聯
        self.assertEqual(session_data['scenario']['id'], str(self.scenario.id))
        self.assertEqual(session_data['scenario']['name'], self.scenario.name)
        
        # 驗證訊息關聯
        messages = session_data['messages']
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['id'], str(message.id))
        self.assertEqual(messages[0]['content'], message.content)