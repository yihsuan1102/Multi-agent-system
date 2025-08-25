from rolepermissions.roles import AbstractUserRole


class Admin(AbstractUserRole):
    available_permissions = {
        # 全文檢索操作
        "search_all_conversations": True,
        "search_group_conversations": True,
        "search_own_conversations": True,
        # 場景管理操作
        "create_scenario": True,
        "modify_scenario": True,
        "delete_scenario": True,
        "adjust_scenario_routing": True,
        "set_scenario_global": True,
        # 群組管理操作
        "create_group": True,
        "manage_group": True,
        "assign_user_to_group": True,
        "assign_scenario_to_group": True,
        # 群組內場景分配操作
        "assign_scenario_to_group_member": True,
        "manage_group_scenario_access": True,
        # 對話操作
        "send_message_to_scenario": True,
        "use_scenario": True,
        # 歷史對話檢視操作
        "view_all_conversations": True,
        "view_group_conversations": True,
        "view_own_conversations": True,
    }


class Supervisor(AbstractUserRole):
    available_permissions = {
        # 全文檢索操作
        "search_group_conversations": True,
        "search_own_conversations": True,
        # 場景管理操作（受限於群組內可存取之場景）
        "modify_scenario": True,
        # 群組內場景分配操作
        "assign_scenario_to_group_member": True,
        "manage_group_scenario_access": True,
        # 對話操作
        "send_message_to_scenario": True,
        "use_scenario": True,
        # 歷史對話檢視操作
        "view_group_conversations": True,
        "view_own_conversations": True,
    }


class Employee(AbstractUserRole):
    available_permissions = {
        # 全文檢索操作
        "search_own_conversations": True,
        # 對話操作
        "send_message_to_scenario": True,
        "use_scenario": True,
        # 歷史對話檢視操作
        "view_own_conversations": True,
    }


