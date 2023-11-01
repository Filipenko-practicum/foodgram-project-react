from django.forms import ModelForm

from .models import ImportIngredient, ImportTag


class IngredientImportForm(ModelForm):
    """Форма добавления ингридиентов при импорте."""

    class Meta:
        model = ImportIngredient
        fields = ('csv_file',)


class TagImportForm(ModelForm):
    """Форма добавления тегов при импорте."""

    class Meta:
        model = ImportTag
        fields = ('csv_file',)
