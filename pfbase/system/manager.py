from django.db import models


class OrganizationManager(models.Manager):
    def getById(self, id: int):
        return self.get(id=id).code

    def getByIdentifier(self, identifier: str):
        return self.filter(identifier=identifier)

    def getByCode(self, code: str):
        return self.get(code=code).id

