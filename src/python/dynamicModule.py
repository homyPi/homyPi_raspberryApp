import imp

class DynamicModule:

	def __init__(self, modules=[]):
		"""
		modules - List of modules informations:
			{
				module: module name,
				className: class name,
				path: path of the file containing the module
			}
		"""
		self.modules = modules;


	def load(self):
		"""
		will load the module class and put it in module.class
		return: modules list
		"""
		for module in self.modules:
			print "loading " + module["moduleName"] + " from " + module["path"]
			foo = imp.load_source(module["moduleName"], module["path"])
			cls = getattr(foo, module["className"])
			module["class"] = cls
		return self.modules
