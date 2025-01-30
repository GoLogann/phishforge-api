class PhishingEmail:
    def __init__(self, receptor: str, remetente: str, assunto: str, conteudo: str, links: list):
        self.receptor = receptor
        self.remetente = remetente
        self.assunto = assunto
        self.conteudo = conteudo
        self.links = links

    def __repr__(self):
        return f"PhishingEmail(receptor={self.receptor}, remetente={self.remetente}, assunto={self.assunto}, conteudo={self.conteudo}, links={self.links})"