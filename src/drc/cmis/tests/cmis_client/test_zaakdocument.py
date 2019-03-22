from datetime import date, datetime
from io import BytesIO
from unittest import skipIf

from django.conf import settings
from django.test import TestCase, override_settings

import pytz

from drc.datamodel.tests.factories import EnkelvoudigInformatieObjectFactory

from ...exceptions import DocumentExistsError
from .mixins import DMSMixin


@skipIf(not settings.CMIS_BACKEND_ENABLED, "Skipped if CMIS should not be active")
class CMISClientTests(DMSMixin, TestCase):
    def test_maak_zaakdocument(self):
        """
        4.3.5.3 - test dat het aanmaken van een zaakdocument mogelijk is.
        """
        self.client.creeer_zaakfolder(self.zaak_url)

        document = EnkelvoudigInformatieObjectFactory.create(
            titel='testnaam',
            identificatie='31415926535',
            ontvangstdatum=date(2017, 1, 1),
            beschrijving='Een beschrijving',
        )

        cmis_doc = self.client.maak_zaakdocument(document, self.zaak_url)
        # no actual binary data is added
        # we have to set an (empty) stream, otherwise cmislib blocks us from setting/reading the stream
        # self.assertIsNone(cmis_doc.properties['cmis:contentStreamFileName'])

        # verify that it identifications are unique
        with self.assertRaises(DocumentExistsError):
            self.client.maak_zaakdocument(document, self.zaak_url)

        # verify expected props
        self.assertExpectedProps(cmis_doc, {
            # when no contentstreamfilename is provided, it is apparently set to the document name
            'cmis:contentStreamFileName': 'testnaam',
            # 'cmis:contentStreamId': None,
            'cmis:contentStreamLength': 0,  # because we created an empty object
            'cmis:contentStreamMimeType': 'application/binary',  # the default if it couldn't be determined
            # 'zsdms:dct.categorie': document.informatieobjecttype.informatieobjectcategorie,
            'zsdms:dct.omschrijving': document.informatieobjecttype,
            'zsdms:documentIdentificatie': '31415926535',
            'zsdms:documentauteur': document.auteur,
            'zsdms:documentbeschrijving': 'Een beschrijving',
            'zsdms:documentcreatiedatum': datetime.combine(document.creatiedatum, datetime.min.time()).replace(tzinfo=pytz.utc),
            # 'zsdms:documentformaat': None,
            'zsdms:documentLink': None,
            'zsdms:documentontvangstdatum': datetime.combine(document.ontvangstdatum, datetime.min.time()).replace(tzinfo=pytz.utc),
            'zsdms:documentstatus': None,
            'zsdms:documenttaal': document.taal,
            'zsdms:documentversie': None,
            'zsdms:documentverzenddatum': None,
            'zsdms:vertrouwelijkaanduiding': document.vertrouwelijkheidaanduiding
        })

        document.refresh_from_db()
        self.assertEqual(
            document._object_id,
            cmis_doc.properties['cmis:objectId'].rsplit(';')[0]
        )

    def test_maak_zaakdocument_met_gevulde_inhoud(self):
        self.client.creeer_zaakfolder(self.zaak_url)

        document = EnkelvoudigInformatieObjectFactory.create(
            titel='testnaam',
            identificatie='31415926535',
            ontvangstdatum=date(2017, 1, 1),
            beschrijving='Een beschrijving',
        )

        cmis_doc = self.client.maak_zaakdocument_met_inhoud(document, self.zaak_url, stream=BytesIO(b'test'))
        self.assertExpectedProps(cmis_doc, {
            'cmis:contentStreamFileName': 'testnaam',
            'cmis:contentStreamLength': 4,  # because we created an empty object
            'cmis:contentStreamMimeType': 'application/binary',  # the default if it couldn't be determined
            'zsdms:dct.omschrijving': document.informatieobjecttype,
            'zsdms:documentIdentificatie': '31415926535',
            'zsdms:documentauteur': document.auteur,
            'zsdms:documentbeschrijving': 'Een beschrijving',
            'zsdms:documentcreatiedatum': datetime.combine(document.creatiedatum, datetime.min.time()).replace(tzinfo=pytz.utc),
            'zsdms:documentLink': None,
            'zsdms:documentontvangstdatum': datetime.combine(document.ontvangstdatum, datetime.min.time()).replace(tzinfo=pytz.utc),
            'zsdms:documentstatus': None,
            'zsdms:documenttaal': document.taal,
            'zsdms:documentversie': None,
            'zsdms:documentverzenddatum': None,
            'zsdms:vertrouwelijkaanduiding': document.vertrouwelijkheidaanduiding
        })

        document.refresh_from_db()
        self.assertEqual(
            document._object_id,
            cmis_doc.properties['cmis:objectId'].rsplit(';')[0]
        )

    @override_settings(CMIS_SENDER_PROPERTY='zsdms:documentauteur')
    def test_maak_zaakdocument_met_sender_property(self):
        self.client.creeer_zaakfolder(self.zaak_url)

        document = EnkelvoudigInformatieObjectFactory.create(
            titel='testnaam',
            identificatie='31415926535',
            ontvangstdatum=date(2017, 1, 1),
            beschrijving='Een beschrijving',
        )

        cmis_doc = self.client.maak_zaakdocument_met_inhoud(document, self.zaak_url, sender='maykin', stream=BytesIO(b'test'))
        self.assertExpectedProps(cmis_doc, {
            'cmis:contentStreamFileName': 'testnaam',
            'cmis:contentStreamLength': 4,
            'cmis:contentStreamMimeType': 'application/binary',
            'zsdms:dct.omschrijving': document.informatieobjecttype,
            'zsdms:documentIdentificatie': '31415926535',
            'zsdms:documentauteur': 'maykin',  # overridden by the sender
            'zsdms:documentbeschrijving': 'Een beschrijving',
            'zsdms:documentcreatiedatum': datetime.combine(document.creatiedatum, datetime.min.time()).replace(tzinfo=pytz.utc),
            'zsdms:documentLink': None,
            'zsdms:documentontvangstdatum': datetime.combine(document.ontvangstdatum, datetime.min.time()).replace(tzinfo=pytz.utc),
            'zsdms:documentstatus': None,
            'zsdms:documenttaal': document.taal,
            'zsdms:documentversie': None,
            'zsdms:documentverzenddatum': None,
            'zsdms:vertrouwelijkaanduiding': document.vertrouwelijkheidaanduiding
        })

        document.refresh_from_db()
        self.assertEqual(
            document._object_id,
            cmis_doc.properties['cmis:objectId'].rsplit(';')[0]
        )

    def test_lees_document(self):
        """
        Ref #83: geefZaakdocumentLezen vraagt een kopie van het bestand op.

        Van het bestand uit het DMS wordt opgevraagd: inhoud, bestandsnaam.
        """
        self.client.creeer_zaakfolder(self.zaak_url)
        document = EnkelvoudigInformatieObjectFactory.create(identificatie='123456')
        cmis_doc = self.client.maak_zaakdocument(document, self.zaak_url)

        # empty by default
        filename, file_obj = self.client.geef_inhoud(document)

        self.assertEqual(filename, document.titel)
        self.assertEqual(file_obj.read(), b'')

        cmis_doc.setContentStream(BytesIO(b'some content'), 'text/plain')

        filename, file_obj = self.client.geef_inhoud(document)

        self.assertEqual(filename, document.titel)
        self.assertEqual(file_obj.read(), b'some content')

    def test_lees_document_bestaad_niet(self):
        """
        Ref #83: geefZaakdocumentLezen vraagt een kopie van het bestand op.

        Van het bestand uit het DMS wordt opgevraagd: inhoud, bestandsnaam.
        """
        self.client.creeer_zaakfolder(self.zaak_url)
        document = EnkelvoudigInformatieObjectFactory.build(identificatie='123456')

        # empty by default
        filename, file_obj = self.client.geef_inhoud(document)

        self.assertEqual(filename, None)
        self.assertEqual(file_obj.read(), b'')

    def test_voeg_zaakdocument_toe(self):
        """
        4.3.4.3 Interactie tussen ZS en DMS

        Het ZS zorgt ervoor dat het document dat is aangeboden door de DSC wordt vastgelegd in het DMS.
        Hiervoor maakt het ZS gebruik van de CMIS-services die aangeboden worden door het DMS. Hierbij
        gelden de volgende eisen:
        - Het document wordt gerelateerd aan de juiste Zaakfolder (Zie 5.1)
        - Het document wordt opgeslagen als objecttype EDC (Zie 5.2)
        - Minimaal de vereiste metadata voor een EDC wordt vastgelegd in de daarvoor gedefinieerde
        objectproperties. In Tabel 3 is een mapping aangegeven tussen de StUF-ZKN-elementen en
        CMIS-objectproperties.
        """
        document = EnkelvoudigInformatieObjectFactory.create(
            titel='testnaam', identificatie='31415926535', beschrijving='Een beschrijving'
        )
        self.client.maak_zaakdocument(document)
        document.refresh_from_db()

        result = self.client.zet_inhoud(document, BytesIO(b'some content'), content_type='text/plain')

        self.assertIsNone(result)
        filename, file_obj = self.client.geef_inhoud(document)
        self.assertEqual(file_obj.read(), b'some content')
        self.assertEqual(filename, document.titel)

    def test_relateer_aan_zaak(self):
        document = EnkelvoudigInformatieObjectFactory.create(
            titel='testnaam', identificatie='31415926535', beschrijving='Een beschrijving'
        )
        zaak_folder = self.client.creeer_zaakfolder(self.zaak_url)
        self.client.maak_zaakdocument(document)
        document.refresh_from_db()

        result = self.client.relateer_aan_zaak(document, self.zaak_url)
        self.assertIsNone(result)

        cmis_doc = self.client._get_cmis_doc(document)
        parents = [parent.id for parent in cmis_doc.getObjectParents()]
        self.assertEqual(parents, [zaak_folder.id])

    def test_ontkoppel_zaakdocument(self):
        cmis_folder = self.client.creeer_zaakfolder(self.zaak_url)
        document = EnkelvoudigInformatieObjectFactory.create(
            titel='testnaam', identificatie='31415926535', beschrijving='Een beschrijving'
        )
        self.client.maak_zaakdocument(document, self.zaak_url)
        result = self.client.ontkoppel_zaakdocument(document, self.zaak_url)
        self.assertIsNone(result)

        # check that the zaakfolder is empty
        self.assertFalse(cmis_folder.getChildren())

    def test_verwijder_document(self):
        zaak_folder = self.client.creeer_zaakfolder(self.zaak_url)
        document = EnkelvoudigInformatieObjectFactory.create(
            titel='testnaam', identificatie='31415926535', beschrijving='Een beschrijving'
        )
        self.client.maak_zaakdocument(document, self.zaak_url)

        result = self.client.verwijder_document(document)

        self.assertIsNone(result)
        # check that it's gone
        trash_folder, _ = self.client._get_or_create_folder(self.client.TRASH_FOLDER)
        self.assertEqual(len(trash_folder.getChildren()), 0)
        self.assertEqual(len(zaak_folder.getChildren()), 0)
