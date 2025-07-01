def classFactory(iface):
    from .rest_loader import RestLoader
    return RestLoader(iface)
