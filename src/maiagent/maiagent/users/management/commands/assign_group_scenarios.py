from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from maiagent.chat.models import Group, GroupScenarioAccess, Scenario


class Command(BaseCommand):
    help = "將指定 scenario 分配給指定 group：--group <uuid|slug> --scenario <uuid|name>"

    def add_arguments(self, parser):  # type: ignore[override]
        parser.add_argument("--group", required=True)
        parser.add_argument("--scenario", required=True)

    def handle(self, *args, **options):
        group_id_or_name = options["group"]
        scenario_id_or_name = options["scenario"]

        group = Group.objects.filter(id=group_id_or_name).first() or Group.objects.filter(name=group_id_or_name).first()
        if not group:
            raise CommandError("Group 不存在")
        scenario = (
            Scenario.objects.filter(id=scenario_id_or_name).first()
            or Scenario.objects.filter(name=scenario_id_or_name).first()
        )
        if not scenario:
            raise CommandError("Scenario 不存在")

        GroupScenarioAccess.objects.get_or_create(group=group, scenario=scenario)
        self.stdout.write(self.style.SUCCESS(f"已授權：{group.name} -> {scenario.name}"))


