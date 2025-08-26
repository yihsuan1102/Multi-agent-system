"""
彈性訊息提交 API 測試
測試 API 1 的各種情境，包含錯誤處理
"""
import json
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
    LlmModelFactory, 
    ScenarioFactory,
    SessionFactory,
    UserFactory,
)
from maiagent.users.models import User

User = get_user_model()


class MessageSubmissionAPITestCase(APITestCase):
    """訊息提交 API 測試案例"""
    
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
        self.session = SessionFactory(
            user=self.user,
            scenario=self.scenario,
            status=Session.Status.ACTIVE
        )
        
        # 建立 LLM 模型
        self.llm_model = LlmModelFactory()
        
        # 取得 JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # 設定認證標頭
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_submit_message_with_existing_session_url(self):
        """測試使用現有會話（URL中的session_id）"""
        url = reverse('api:conversation-post-message', kwargs={'pk': str(self.session.id)})
        data = {
            'content': '測試訊息內容'
        }
        
        with patch('maiagent.chat.tasks.process_message.delay') as mock_delay:
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        response_data = response.json()
        self.assertEqual(response_data['session_id'], str(self.session.id))
        self.assertEqual(response_data['message']['content'], '測試訊息內容')
        self.assertEqual(response_data['message']['role'], 'user')
        
        # 驗證訊息已儲存到資料庫
        message = Message.objects.get(id=response_data['message']['id'])
        self.assertEqual(message.content, '測試訊息內容')
        self.assertEqual(message.session, self.session)
        
        # 驗證 Celery 任務已發送
        mock_delay.assert_called_once()
    
    def test_submit_message_with_session_id_in_body(self):
        """測試使用現有會話（請求體中的session_id）"""
        url = reverse('api:conversation-post-message-no-session')
        data = {
            'content': '測試訊息內容',
            'session_id': str(self.session.id)
        }
        
        with patch('maiagent.chat.tasks.process_message.delay') as mock_delay:
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        response_data = response.json()
        self.assertEqual(response_data['session_id'], str(self.session.id))
        self.assertEqual(response_data['message']['content'], '測試訊息內容')
        
        # 驗證 Celery 任務已發送
        mock_delay.assert_called_once()
    
    def test_submit_message_create_new_session(self):
        """測試建立新會話"""
        url = reverse('api:conversation-post-message-no-session')
        data = {
            'content': '新會話測試訊息',
            'scenario_id': str(self.scenario.id)
        }
        
        with patch('maiagent.chat.tasks.process_message.delay') as mock_delay:
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        response_data = response.json()
        # 驗證回傳了新的 session_id
        new_session_id = response_data['session_id']
        self.assertNotEqual(new_session_id, str(self.session.id))
        
        # 驗證新會話已建立
        new_session = Session.objects.get(id=new_session_id)
        self.assertEqual(new_session.user, self.user)
        self.assertEqual(new_session.scenario, self.scenario)
        self.assertEqual(new_session.status, Session.Status.WAITING)
        
        # 驗證訊息已儲存
        self.assertEqual(response_data['message']['content'], '新會話測試訊息')
        
        # 驗證 Celery 任務已發送
        mock_delay.assert_called_once()
    
    def test_submit_message_with_llm_model_id(self):
        """測試指定 LLM 模型"""
        url = reverse('api:conversation-post-message-no-session')
        data = {
            'content': '指定模型測試',
            'scenario_id': str(self.scenario.id),
            'llm_model_id': str(self.llm_model.id)
        }
        
        with patch('maiagent.chat.tasks.process_message.delay') as mock_delay:
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_delay.assert_called_once()


class MessageSubmissionErrorHandlingTestCase(APITestCase):
    """訊息提交 API 錯誤處理測試"""
    
    def setUp(self):
        """測試前準備"""
        self.group = GroupFactory()
        self.user = UserFactory(group=self.group)
        self.scenario = ScenarioFactory()
        
        # 設定認證
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_submit_message_without_authentication(self):
        """測試未認證的請求"""
        # 移除認證標頭
        self.client.credentials()
        
        url = reverse('api:conversation-post-message-no-session')
        data = {'content': '測試訊息'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_submit_message_empty_content(self):
        """測試空白內容"""
        url = reverse('api:conversation-post-message-no-session')
        data = {
            'content': '',
            'scenario_id': str(self.scenario.id)
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('content', response_data)
    
    def test_submit_message_missing_scenario_for_new_session(self):
        """測試建立新會話時缺少 scenario_id"""
        url = reverse('api:conversation-post-message-no-session')
        data = {'content': '測試訊息'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('scenario_id', response_data)
    
    def test_submit_message_nonexistent_session(self):
        """測試不存在的會話"""
        fake_session_id = str(uuid.uuid4())
        url = reverse('api:conversation-post-message-no-session')
        data = {
            'content': '測試訊息',
            'session_id': fake_session_id
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        response_data = response.json()
        self.assertEqual(response_data['detail'], '會話不存在')
    
    def test_submit_message_nonexistent_scenario(self):
        """測試不存在的場景"""
        fake_scenario_id = str(uuid.uuid4())
        url = reverse('api:conversation-post-message-no-session')
        data = {
            'content': '測試訊息',
            'scenario_id': fake_scenario_id
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_submit_message_no_scenario_access(self):
        """測試無場景存取權"""
        # 建立另一個群組的場景（使用者沒有存取權）
        other_group = GroupFactory()
        restricted_scenario = ScenarioFactory()
        GroupScenarioAccess.objects.create(
            group=other_group,
            scenario=restricted_scenario
        )
        
        url = reverse('api:conversation-post-message-no-session')
        data = {
            'content': '測試訊息',
            'scenario_id': str(restricted_scenario.id)
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        response_data = response.json()
        self.assertEqual(response_data['detail'], '無場景存取權')
    
    def test_submit_message_closed_session(self):
        """測試已關閉的會話"""
        # 建立已關閉的會話
        closed_session = SessionFactory(
            user=self.user,
            scenario=self.scenario,
            status=Session.Status.CLOSED
        )
        
        # 建立群組場景存取權
        GroupScenarioAccess.objects.create(
            group=self.group,
            scenario=self.scenario
        )
        
        url = reverse('api:conversation-post-message', kwargs={'pk': str(closed_session.id)})
        data = {'content': '測試訊息'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertEqual(response_data['detail'], '會話狀態不允許提交訊息')
    
    def test_submit_message_celery_failure(self):
        """測試 Celery 服務失敗"""
        # 建立群組場景存取權
        GroupScenarioAccess.objects.create(
            group=self.group,
            scenario=self.scenario
        )
        
        url = reverse('api:conversation-post-message-no-session')
        data = {
            'content': '測試訊息',
            'scenario_id': str(self.scenario.id)
        }
        
        # 模擬 Celery 失敗
        with patch('maiagent.chat.tasks.process_message.delay') as mock_delay:
            mock_delay.side_effect = Exception("Celery broker not available")
            
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        
        response_data = response.json()
        self.assertIn('訊息處理服務暫時不可用', response_data['detail'])
    
    def test_submit_message_nonexistent_llm_model(self):
        """測試不存在的 LLM 模型"""
        # 建立群組場景存取權
        GroupScenarioAccess.objects.create(
            group=self.group,
            scenario=self.scenario
        )
        
        fake_llm_id = str(uuid.uuid4())
        url = reverse('api:conversation-post-message-no-session')
        data = {
            'content': '測試訊息',
            'scenario_id': str(self.scenario.id),
            'llm_model_id': fake_llm_id
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MessageSubmissionIntegrationTestCase(APITestCase):
    """訊息提交 API 整合測試"""
    
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
    
    def test_complete_conversation_flow(self):
        """測試完整對話流程"""
        url = reverse('api:conversation-post-message-no-session')
        
        # 第一條訊息 - 建立新會話
        data1 = {
            'content': '你好，我有問題想諮詢',
            'scenario_id': str(self.scenario.id)
        }
        
        with patch('maiagent.chat.tasks.process_message.delay') as mock_delay:
            response1 = self.client.post(url, data1, format='json')
        
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        session_id = response1.json()['session_id']
        
        # 第二條訊息 - 使用現有會話
        data2 = {
            'content': '可以說明一下產品特色嗎？',
            'session_id': session_id
        }
        
        with patch('maiagent.chat.tasks.process_message.delay') as mock_delay:
            response2 = self.client.post(url, data2, format='json')
        
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.json()['session_id'], session_id)
        
        # 驗證會話中有兩條訊息
        messages = Message.objects.filter(session_id=session_id).order_by('sequence_number')
        self.assertEqual(messages.count(), 2)
        self.assertEqual(messages[0].content, '你好，我有問題想諮詢')
        self.assertEqual(messages[1].content, '可以說明一下產品特色嗎？')