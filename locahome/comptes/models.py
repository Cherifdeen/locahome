from django.contrib.auth.models import User
from django.db import models


class Proprietaire(models.Model):
    """
    Profil propriétaire lié à un compte utilisateur Django.
    Chaque propriétaire peut gérer plusieurs maisons.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="proprietaire",
    )
    nom_complet = models.CharField(max_length=150)
    telephone = models.CharField(max_length=30, blank=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Propriétaire"
        verbose_name_plural = "Propriétaires"

    def __str__(self) -> str:
        return self.nom_complet

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("comptes:profil")
