import pkgutil

for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    if not is_pkg:
        globals()[module_name] = loader.find_module(module_name).load_module(module_name)

