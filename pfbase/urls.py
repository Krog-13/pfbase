"""
Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from django.urls import path, include
from rest_framework import routers
from .dictionary.urls import dct_router, idc_router, his_router, elm_router, eiv_router, elm_urlpatterns
from .document.urls import dcm_router, rct_router, dcm_idc_router, riv_router, dcm_his_router, rct_urlpatterns, dynamic_router_urlpatterns
from .system.urls import ntf_router, lv_router, org_router, user_router, user_urlpatterns, common_urlpatterns
from .docs.urls import doc_urlpatterns

router = routers.DefaultRouter()
router.registry.extend(dct_router.registry)
router.registry.extend(idc_router.registry)
router.registry.extend(elm_router.registry)
router.registry.extend(eiv_router.registry)
router.registry.extend(his_router.registry)

router.registry.extend(dcm_router.registry)
router.registry.extend(rct_router.registry)
router.registry.extend(dcm_idc_router.registry)
router.registry.extend(riv_router.registry)
router.registry.extend(dcm_his_router.registry)

router.registry.extend(ntf_router.registry)
router.registry.extend(lv_router.registry)
router.registry.extend(org_router.registry)
router.registry.extend(user_router.registry)

urlpatterns = [
    path("", include(router.urls)),
]

urlpatterns += elm_urlpatterns + rct_urlpatterns + doc_urlpatterns + user_urlpatterns + common_urlpatterns + dynamic_router_urlpatterns
