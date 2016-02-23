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
		self.modules = []
		if modules is None:
			modules = []
		print "==================="
		print str(len(modules))
		print "==================="
		for module in modules:
			print str(module)
			if "moduleName" in module and "path" in module and "className" in module:
				self.modules.append(module)
			else:
				print "invalid module"

	def load(self):
		"""
		will load the modules classes and put it in module.class
		return: modules list
		"""
		for module in self.modules:
			print "loading " + module["moduleName"] + " from " + module["path"]
			foo = imp.load_source(module["moduleName"], module["path"])
			cls = getattr(foo, module["className"])
			module["class"] = cls
		return self.modules

	def getClass(self, moduleName):
		for module in self.modules:
			if module["moduleName"] == moduleName:
				return module["class"]

		return None;
