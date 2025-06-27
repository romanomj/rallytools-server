from django.db import models



##########################################
########## Player/Class Models ###########
##########################################

class PlayableRace(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=24, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Playable Races"

class PlayableClass(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=14, unique=True, db_index=True)
    icon = models.CharField(max_length=128)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Playable Classes"


class PlayableSpecialization(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=16, db_index=True)
    icon = models.CharField(max_length=128)

    playable_class = models.ForeignKey(PlayableClass, on_delete=models.CASCADE, related_name='spec')
    role = models.CharField(max_length=8, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Playable Specializations"

##########################################
######## Profession/Recipe Models ########
##########################################

class Profession(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=16)
    icon = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class ProfessionSkillTier(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=32)
    profession = models.ForeignKey(Profession, on_delete=models.CASCADE, related_name='tier')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Profession Skill Tiers"


class Reagent(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

class Recipe(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=96, db_index=True)
    icon =  models.CharField(max_length=128)
    profession = models.ForeignKey(Profession, on_delete=models.CASCADE, null=True)
    profession_skill_tier = models.ForeignKey(ProfessionSkillTier, on_delete=models.CASCADE, null=True)
    crafted_quantity = models.DecimalField(default=1.0, max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name

class RecipeReagent(models.Model):
    id = models.AutoField(primary_key=True)
    reagent = models.ForeignKey(Reagent, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.recipe.name} - {self.reagent.name}"
    

####
class Item(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=64, db_index=True)
    icon = models.CharField(max_length=128)
    item_class = models.CharField(max_length=32, db_index=True)
    item_subclass = models.CharField(max_length=32, db_index=True)

    def __str__(self):
        return self.name
