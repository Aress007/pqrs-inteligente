from django.test import TestCase
from transformers import pipeline


class ClasificadorTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.classifier = pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
        )

    def test_reclamo(self):

        resultado = self.classifier(
            "Me cobraron dos veces el mismo servicio",
            [
                "petición de información o solicitud de servicio",
                "queja por mala atención o inconformidad",
                "reclamo por incumplimiento, cobro o producto defectuoso",
                "sugerencia para mejorar el servicio"
            ]
        )

        print(resultado)

        self.assertTrue(len(resultado["labels"]) > 0)