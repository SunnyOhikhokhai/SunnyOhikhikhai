"""Values available in every template."""


def finplan(request):
    match = getattr(request, "resolver_match", None)
    return {
        "BRAND_NAME": "FINPLAN",
        "BRAND_PROMISE": "Plan Smarter. Grow Further.",
        "nav_section": match.app_name if match else "",
    }
