#!/usr/bin/env python
"""
Simple test script to verify the scenario update endpoint works.
"""

import os
import sys
import django
import uuid
from django.test import TestCase, Client
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import Group as DjangoGroup
from rolepermissions.roles import assign_role

# Add the project directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'maiagent'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from maiagent.users.tests.factories import UserFactory
from maiagent.chat.tests.factories import (
    ScenarioFactory, 
    LlmModelFactory, 
    ScenarioModelFactory, 
    GroupFactory,
    GroupScenarioAccessFactory
)
from maiagent.users.models import User
from maiagent.chat.models import Scenario, LlmModel, ScenarioModel


class ScenarioUpdateTestCase(APITestCase):
    def setUp(self):
        """Set up test data"""
        # Create groups
        self.admin_group = GroupFactory(name="管理員群組")
        self.supervisor_group = GroupFactory(name="主管群組")
        
        # Create users with different roles
        self.admin_user = UserFactory(
            role=User.Role.ADMIN,
            group=self.admin_group,
            username="admin_user"
        )
        self.supervisor_user = UserFactory(
            role=User.Role.SUPERVISOR, 
            group=self.supervisor_group,
            username="supervisor_user"
        )
        self.employee_user = UserFactory(
            role=User.Role.EMPLOYEE,
            group=self.supervisor_group,  # Same group as supervisor
            username="employee_user"
        )
        
        # Assign roles using rolepermissions
        assign_role(self.admin_user, 'admin')
        assign_role(self.supervisor_user, 'supervisor')
        assign_role(self.employee_user, 'employee')
        
        # Create scenarios
        self.scenario = ScenarioFactory(name="測試場景")
        
        # Grant access to supervisor group
        GroupScenarioAccessFactory(
            group=self.supervisor_group,
            scenario=self.scenario
        )
        
        # Create LLM models
        self.model1 = LlmModelFactory(provider="openai", name="gpt-4")
        self.model2 = LlmModelFactory(provider="anthropic", name="claude-3")
        
        # Create scenario models
        self.scenario_model1 = ScenarioModelFactory(
            scenario=self.scenario,
            llm_model=self.model1,
            is_default=True
        )
        self.scenario_model2 = ScenarioModelFactory(
            scenario=self.scenario, 
            llm_model=self.model2,
            is_default=False
        )
        
        print(f"✅ Setup completed:")
        print(f"  Scenario: {self.scenario.id} - {self.scenario.name}")
        print(f"  Model 1: {self.model1.id} - {self.model1.provider}:{self.model1.name} (default)")
        print(f"  Model 2: {self.model2.id} - {self.model2.provider}:{self.model2.name}")
    
    def test_admin_can_update_scenario_model(self):
        """Test that admin can update scenario model"""
        print("\n🔥 Testing admin scenario update...")
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = f"/api/v1/scenarios/{self.scenario.id}/"
        data = {"model_id": str(self.model2.id)}
        
        response = self.client.put(url, data, format='json')
        
        print(f"  Request URL: {url}")
        print(f"  Request data: {data}")
        print(f"  Response status: {response.status_code}")
        print(f"  Response data: {response.json() if response.content else 'No content'}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the model was updated
        updated_scenario_model = ScenarioModel.objects.get(
            scenario=self.scenario,
            llm_model=self.model2,
            is_default=True
        )
        
        # Verify old default was changed
        old_default = ScenarioModel.objects.get(
            scenario=self.scenario,
            llm_model=self.model1
        )
        self.assertFalse(old_default.is_default)
        
        print("  ✅ Admin update successful")
    
    def test_supervisor_can_update_authorized_scenario(self):
        """Test that supervisor can update scenario they have access to"""
        print("\n🔥 Testing supervisor scenario update...")
        
        self.client.force_authenticate(user=self.supervisor_user)
        
        url = f"/api/v1/scenarios/{self.scenario.id}/"
        data = {"model_id": str(self.model2.id)}
        
        response = self.client.put(url, data, format='json')
        
        print(f"  Request URL: {url}")
        print(f"  Request data: {data}")
        print(f"  Response status: {response.status_code}")
        print(f"  Response data: {response.json() if response.content else 'No content'}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("  ✅ Supervisor update successful")
    
    def test_employee_cannot_update_scenario(self):
        """Test that employee cannot update scenario"""
        print("\n🔥 Testing employee scenario update (should fail)...")
        
        self.client.force_authenticate(user=self.employee_user)
        
        url = f"/api/v1/scenarios/{self.scenario.id}/"
        data = {"model_id": str(self.model2.id)}
        
        response = self.client.put(url, data, format='json')
        
        print(f"  Request URL: {url}")
        print(f"  Request data: {data}")
        print(f"  Response status: {response.status_code}")
        print(f"  Response data: {response.json() if response.content else 'No content'}")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("  ✅ Employee correctly denied access")
    
    def test_invalid_model_id_rejected(self):
        """Test that invalid model ID is rejected"""
        print("\n🔥 Testing invalid model ID...")
        
        self.client.force_authenticate(user=self.admin_user)
        
        fake_model_id = str(uuid.uuid4())
        url = f"/api/v1/scenarios/{self.scenario.id}/"
        data = {"model_id": fake_model_id}
        
        response = self.client.put(url, data, format='json')
        
        print(f"  Request URL: {url}")
        print(f"  Request data: {data}")
        print(f"  Response status: {response.status_code}")
        print(f"  Response data: {response.json() if response.content else 'No content'}")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn("model_id", response_data.get("errors", {}))
        self.assertIn("指定的模型不存在", response_data["errors"]["model_id"])
        print("  ✅ Invalid model ID correctly rejected")


if __name__ == "__main__":
    import django
    from django.test.utils import get_runner
    from django.conf import settings
    
    # Initialize Django test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run specific test case
    test_case = ScenarioUpdateTestCase()
    test_case.setUp()
    
    print("🚀 Running scenario update tests...\n")
    
    try:
        test_case.test_admin_can_update_scenario_model()
        test_case.test_supervisor_can_update_authorized_scenario() 
        test_case.test_employee_cannot_update_scenario()
        test_case.test_invalid_model_id_rejected()
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()