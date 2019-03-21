from backend.utils.AgentOntoLang import AgentOntoLang


class KnowledgeLoader(object):

    loaded = []

    @classmethod
    def load_script(cls, script: str):
        AgentOntoLang().run(script)

    @classmethod
    def load_resource(cls, package: str, file: str):
        AgentOntoLang().load_knowledge(package, file)
        KnowledgeLoader.loaded.append(package + "." + file)

    @classmethod
    def list_resources(cls, package: str):
        from pkg_resources import resource_listdir
        return list(map(lambda f: (package, f), filter(lambda f: f.endswith(".knowledge") or f.endswith(".environment"), resource_listdir(package, ''))))
