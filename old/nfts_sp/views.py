from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def emitir_nfts(request):
    """Tela para emissão de NFT-e São Paulo"""
    context = {
        'user': request.user,
        'empresa': request.user.profile.empresa if hasattr(request.user, 'profile') else None,
    }
    return render(request, 'nfts_sp/emitir.html', context)
