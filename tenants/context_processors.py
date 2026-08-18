def institution_context(request):
    """
    Context processor to inject current institution and settings into templates.
    """
    context = {
        'current_institution': None,
        'institution_settings': None
    }
    
    if request.user.is_authenticated and not request.user.is_super_admin:
        if request.user.institution:
            context['current_institution'] = request.user.institution
            try:
                context['institution_settings'] = request.user.institution.settings
            except Exception:
                context['institution_settings'] = None
                
    return context
