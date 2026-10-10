"""End-to-end tests of pages, saving, ownership and reports."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projects.models import Project

from .test_business import BASE as BUSINESS
from .test_investment import BASE as INVESTMENT
from .test_real_estate import SALES as REAL_ESTATE
from .test_startup import BASE as STARTUP

ALL_MODELS = {
    "business": BUSINESS,
    "startup": STARTUP,
    "real_estate": REAL_ESTATE,
    "investment": INVESTMENT,
}


class PublicPagesTests(TestCase):
    def test_landing_page(self):
        response = self.client.get(reverse("dashboard:landing"))
        self.assertContains(response, "Plan Smarter. Grow Further.")
        self.assertContains(response, "Start Planning")
        for label in ("Business Financial Model", "Startup Financial Model",
                      "Real Estate Financial Model", "Investment Financial Model"):
            self.assertContains(response, label)
        self.assertContains(response, "images/finplan-logo.png")

    def test_private_pages_require_login(self):
        for name, args in [("dashboard:home", []), ("projects:list", []), ("reports:list", []),
                           ("financial_models:choose", []), ("financial_models:new", ["business"])]:
            response = self.client.get(reverse(name, args=args))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn(reverse("accounts:login"), response["Location"])

    def test_signup_logs_in(self):
        response = self.client.post(reverse("accounts:signup"), {
            "username": "ada", "first_name": "Ada", "email": "",
            "password1": "a-Strong-passw0rd!", "password2": "a-Strong-passw0rd!",
        })
        self.assertRedirects(response, reverse("dashboard:home"))
        response = self.client.get(reverse("dashboard:home"))
        self.assertContains(response, "Welcome, Ada")
        self.assertContains(response, "Your financial workspace starts here.")

    def test_login_and_logout(self):
        User.objects.create_user("bola", password="a-Strong-passw0rd!")
        response = self.client.post(reverse("accounts:login"), {"username": "bola", "password": "a-Strong-passw0rd!"})
        self.assertRedirects(response, reverse("dashboard:home"))
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("dashboard:landing"))
        self.assertEqual(self.client.get(reverse("dashboard:home")).status_code, 302)


class WorkspaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("owner", password="a-Strong-passw0rd!")
        self.client.force_login(self.user)

    def create(self, model_type, data):
        return self.client.post(reverse("financial_models:new", args=[model_type]), {**data, "action": "calculate"})

    def test_choose_page_has_four_working_links(self):
        response = self.client.get(reverse("financial_models:choose"))
        for key in ALL_MODELS:
            url = reverse("financial_models:new", args=[key])
            self.assertContains(response, url)
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_unknown_model_404(self):
        self.assertEqual(self.client.get("/models/crypto/new/").status_code, 404)

    def test_every_model_calculates_saves_and_reports(self):
        for key, data in ALL_MODELS.items():
            with self.subTest(model=key):
                response = self.create(key, data)
                project = Project.objects.filter(owner=self.user, model_type=key).latest("id")
                self.assertRedirects(response, reverse("projects:detail", args=[project.pk]))
                self.assertEqual(project.status, Project.Status.CALCULATED)
                detail = self.client.get(reverse("projects:detail", args=[project.pk]))
                self.assertContains(detail, "Key results")
                self.assertContains(detail, "Scenario comparison")
                self.assertContains(detail, "<svg", html=False)
                self.assertContains(self.client.get(reverse("reports:print", args=[project.pk])), "Disclaimer")
                pdf = self.client.get(reverse("reports:pdf", args=[project.pk]))
                self.assertEqual(pdf["Content-Type"], "application/pdf")
                self.assertTrue(pdf.content.startswith(b"%PDF"))
                self.assertIn("attachment", pdf["Content-Disposition"])

    def test_business_results_values(self):
        self.create("business", BUSINESS)
        project = Project.objects.get(owner=self.user)
        response = self.client.get(reverse("projects:detail", args=[project.pk]))
        self.assertContains(response, "₦147,000.00")   # profit after tax
        self.assertContains(response, "₦750,000.00")   # break-even sales
        self.assertContains(response, "13.4%")         # net margin

    def test_currency_is_respected(self):
        self.create("business", {**BUSINESS, "currency": "USD"})
        project = Project.objects.get(owner=self.user)
        self.assertEqual(project.currency, "USD")
        self.assertContains(self.client.get(reverse("projects:detail", args=[project.pk])), "$147,000.00")

    def test_invalid_input_shows_errors_and_saves_nothing(self):
        data = {**BUSINESS, "monthly_sales": ""}
        response = self.create("business", data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertContains(response, "Some answers need attention")
        self.assertFalse(Project.objects.exists())

    def test_draft_then_finish(self):
        response = self.client.post(reverse("financial_models:new", args=["startup"]),
                                    {"project_name": "Half done", "currency": "GBP", "initial_capital": "5000", "action": "draft"})
        project = Project.objects.get(owner=self.user)
        self.assertRedirects(response, reverse("financial_models:edit", args=[project.pk]))
        self.assertEqual(project.status, Project.Status.DRAFT)
        self.assertEqual(project.currency, "GBP")
        # Results are not shown for drafts.
        self.assertRedirects(self.client.get(reverse("projects:detail", args=[project.pk])),
                             reverse("financial_models:edit", args=[project.pk]))
        # Draft appears on the dashboard and its saved value is pre-filled.
        self.assertContains(self.client.get(reverse("dashboard:home")), "Continue where you left off")
        self.assertContains(self.client.get(reverse("financial_models:edit", args=[project.pk])), 'value="5000"')
        # Finishing it calculates the same project.
        response = self.client.post(reverse("financial_models:edit", args=[project.pk]), {**STARTUP, "action": "calculate"})
        self.assertRedirects(response, reverse("projects:detail", args=[project.pk]))
        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.CALCULATED)

    def test_edit_recalculates(self):
        self.create("business", BUSINESS)
        project = Project.objects.get(owner=self.user)
        edit = self.client.get(reverse("financial_models:edit", args=[project.pk]))
        self.assertContains(edit, 'value="1000000"')
        self.client.post(reverse("financial_models:edit", args=[project.pk]),
                         {**BUSINESS, "monthly_sales": "2000000", "action": "calculate"})
        project.refresh_from_db()
        self.assertEqual(project.inputs["monthly_sales"], "2000000")
        # New revenue 2.1M, gross 1.66M, op profit 1.21M, after 30% tax 847,000
        self.assertContains(self.client.get(reverse("projects:detail", args=[project.pk])), "₦847,000.00")

    def test_custom_line_items_saved_and_redisplayed(self):
        self.create("business", {**BUSINESS, "custom_expenses_name": ["Generator fuel"],
                                 "custom_expenses_amount": ["25000"], "custom_expenses_kind": ["operating"]})
        project = Project.objects.get(owner=self.user)
        self.assertEqual(project.inputs["custom_expenses"][0]["name"], "Generator fuel")
        self.assertContains(self.client.get(reverse("financial_models:edit", args=[project.pk])), "Generator fuel")
        self.assertContains(self.client.get(reverse("projects:detail", args=[project.pk])), "Generator fuel")

    def test_duplicate_and_delete(self):
        self.create("investment", INVESTMENT)
        project = Project.objects.get(owner=self.user)
        response = self.client.post(reverse("projects:duplicate", args=[project.pk]))
        copy = Project.objects.exclude(pk=project.pk).get()
        self.assertRedirects(response, reverse("financial_models:edit", args=[copy.pk]))
        self.assertEqual(copy.name, f"Copy of {project.name}")
        self.assertEqual(copy.inputs["initial_investment"], project.inputs["initial_investment"])
        # Duplicate only via POST.
        self.assertEqual(self.client.get(reverse("projects:duplicate", args=[project.pk])).status_code, 405)
        # Delete asks first, then deletes on POST.
        confirm = self.client.get(reverse("projects:delete", args=[copy.pk]))
        self.assertContains(confirm, "cannot be undone")
        self.assertTrue(Project.objects.filter(pk=copy.pk).exists())
        self.assertRedirects(self.client.post(reverse("projects:delete", args=[copy.pk])), reverse("projects:list"))
        self.assertFalse(Project.objects.filter(pk=copy.pk).exists())

    def test_projects_and_reports_lists(self):
        self.create("business", BUSINESS)
        self.client.post(reverse("financial_models:new", args=["startup"]), {"project_name": "Draft only", "action": "draft"})
        listing = self.client.get(reverse("projects:list"))
        self.assertContains(listing, "Bakery")
        self.assertContains(listing, "Draft only")
        filtered = self.client.get(reverse("projects:list") + "?type=startup")
        self.assertNotContains(filtered, "Bakery")
        reports = self.client.get(reverse("reports:list"))
        self.assertContains(reports, "Bakery")
        self.assertNotContains(reports, "Draft only")

    def test_broken_saved_inputs_do_not_crash(self):
        project = Project.objects.create(owner=self.user, name="Broken", model_type="business",
                                         status=Project.Status.CALCULATED, inputs={"monthly_sales": "10"})
        response = self.client.get(reverse("projects:detail", args=[project.pk]))
        self.assertContains(response, "This project needs attention")
        self.assertRedirects(self.client.get(reverse("reports:pdf", args=[project.pk])),
                             reverse("projects:detail", args=[project.pk]))


class OwnershipTests(TestCase):
    """One user must never reach another user's projects by changing the URL."""

    def setUp(self):
        self.owner = User.objects.create_user("owner", password="a-Strong-passw0rd!")
        self.intruder = User.objects.create_user("intruder", password="a-Strong-passw0rd!")
        self.project = Project.objects.create(owner=self.owner, name="Secret plan", model_type="business",
                                              status=Project.Status.CALCULATED, inputs=BUSINESS)
        self.client.force_login(self.intruder)

    def test_other_users_cannot_access(self):
        pk = self.project.pk
        for name in ("projects:detail", "financial_models:edit", "reports:print", "reports:pdf", "projects:delete"):
            self.assertEqual(self.client.get(reverse(name, args=[pk])).status_code, 404, name)
        for name in ("projects:duplicate", "projects:delete", "financial_models:edit"):
            self.assertEqual(self.client.post(reverse(name, args=[pk]), {**BUSINESS, "action": "calculate"}).status_code, 404, name)
        self.assertTrue(Project.objects.filter(pk=pk, name="Secret plan").exists())
        self.assertEqual(Project.objects.count(), 1)

    def test_lists_show_only_own_projects(self):
        self.assertNotContains(self.client.get(reverse("projects:list")), "Secret plan")
        self.assertNotContains(self.client.get(reverse("reports:list")), "Secret plan")
        self.assertNotContains(self.client.get(reverse("dashboard:home")), "Secret plan")

    def test_owner_can_access(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("projects:detail", args=[self.project.pk])).status_code, 200)


class CsrfTests(TestCase):
    def test_post_without_csrf_token_rejected(self):
        user = User.objects.create_user("u", password="a-Strong-passw0rd!")
        client = self.client_class(enforce_csrf_checks=True)
        client.force_login(user)
        response = client.post(reverse("financial_models:new", args=["business"]), {**BUSINESS, "action": "calculate"})
        self.assertEqual(response.status_code, 403)
