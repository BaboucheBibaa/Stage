from toTag import ToTag
import litellm
from bd import Database

class LLM():
    def __init__(self, model):
        self.__model = model
    
    def getTagActions(self, tag : str):
        db = Database()
        tag_list = db.executeFetch("SELECT Action FROM Tag_Actions TA JOIN Tag T ON TA.ID_Tag = T.ID_Tag AND T.NomTag = ?", (tag,))
        return tag_list
    def reponse(self,message : str):
        tags = ToTag(message)
        list_tag_result =list(tags.result.values())
        #list_tag_result = liste de liste contenant chacun un ou plusieurs tags
        for tag_result in list_tag_result:
            for tag in tag_result:
                print(self.getTagActions(tag))
        prompt = litellm.completion(
            model=self.__model,
            messages = [
                {
                    "role": "system",
                    "content": f"""
                    Tu es un compagnon virtuel d'une personne et tu l'accompagnes dans sa vie de tous les jours.
                    
                    Ton objectif est de répondre au message de l'utilisateur.
                    Tu es un humain. Tu dois répondre de manière humaine.
                    """
                },
                {
                    "role": "user",
                    "content": f"""{message}"""
                }
            ]
        )
        return prompt.choices[0].message.content.strip()