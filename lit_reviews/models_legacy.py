from django.db import models

from s3direct.fields import S3DirectField


class Project(models.Model):
    name = models.CharField(max_length=250)
    dueDate = models.DateField(auto_now=False)


# Id 1 = pubmed
# id 2 = maude/accessdata
# id 3 = cochrane
#  4 = pmc


class SummerStub(models.Model):
    field1 = models.TextField(max_length=300, null=True, blank=True)
    field2 = models.TextField(max_length=300, null=True, blank=True)


class Database(models.Model):
    name = models.CharField(max_length=300, null=True, blank=True)


class Search(models.Model):
    # foreing key to REport class at some point.
    projectId = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE)
    databaseId = models.ForeignKey(Database, null=True, blank=True, on_delete=models.CASCADE)

    name = models.CharField(max_length=300, null=True, blank=True)
    date = models.DateField(blank=True, auto_now_add=True)

    terms = models.CharField(max_length=1000)
    pubsYielded = models.IntegerField()
    # irrelevantPubs = models.IntegerField()
    # duplicatePubs = models.IntegerField()
    # relevantPubs = models.IntegerField()

    exportPath = models.FileField(upload_to='uploads/')


class ExclusionReason(models.Model):
    description = models.CharField(max_length=500)


# articles are for the regular dbs like Pubmed, Embase Cochrane
class Article(models.Model):
    # TODO where is our unique ID?  right now this allows collissions for the same article in many projects.
    searchId = models.ForeignKey(Search, on_delete=models.CASCADE)
    articleTitle = models.CharField(max_length=1000, blank=False)
    pubmedId = models.CharField(max_length=50, blank=True)

    articleAbstract = models.CharField(max_length=100000, blank=False)
    citation = models.CharField(max_length=10000, blank=False)
    articleComment = models.CharField(max_length=10000, blank=True)

    isDuplicate = models.NullBooleanField(null=True, blank=True)

    # device categories below (for full text review)
    deviceCat = models.CharField(max_length=5, blank=True, null=True)
    applicationCat = models.CharField(max_length=5, blank=True, null=True)
    populationCat = models.CharField(max_length=5, blank=True, null=True)
    reportCat = models.CharField(max_length=5, blank=True, null=True)

    fullText_URL = models.CharField(max_length=250, blank=True, null=True, default=None)

    #  data contribution categories

    EXPERT = 'EO'
    REVIEW = 'RA'
    QUESTION = 'Q'
    YES = 'Y'
    NO = 'N'
    DATA_SOURCE_CHOICES = (
        (EXPERT, 'Yes (Expert Opinion)'),
        (REVIEW, 'Yes (Review Article)'),
        (QUESTION, 'Yes (Questionnaire)'),
        (YES, 'Yes'),
        (NO, 'No')
    )

    dataContribution_data = models.CharField(max_length=100, choices=DATA_SOURCE_CHOICES, null=True, blank=True)

    outcomeMeasure = models.NullBooleanField(null=True, blank=True)
    appropriateFollowup = models.NullBooleanField(null=True, blank=True)
    statisticalSignificant = models.NullBooleanField(null=True, blank=True)
    clinicalSignificant = models.NullBooleanField(null=True, blank=True)
    # ftrStatus = models.ForeignKey(ReviewStatus)
    NONE = 'N'
    REQUESTED = 'R'
    RECEIVED = 'D'

    RETAINED_STATE_CHOICES = ((NONE, 'None'), (REQUESTED, 'Requested'),
                              (RECEIVED, 'Received'))
    retained_state = models.CharField(
        max_length=1, choices=RETAINED_STATE_CHOICES)

    NONE = 'N'
    INCLUDED = 'I'
    MAYBE = 'M'
    EXCLUDED = 'E'
    INCLUSION_STATE_CHOICES = ((NONE, 'None'), (INCLUDED, 'Included'),
                               (MAYBE, 'Maybe'), (EXCLUDED, 'Excluded'))
    inclusion_state = models.CharField(
        max_length=1, choices=INCLUSION_STATE_CHOICES)


# NEW = 'N'
# INCLUDED = 'I'
# MAYBE = 'M'
# EXCLUDED = 'E'
# AWAITING_FULL_TEXT = 'A'
# FULL_TEXT_RECEIVED = 'R'
# REVIEW_STATUS_CHOICES = (
#     (NEW, 'New'),
#     (INCLUDED, 'Included'),
#     (MAYBE, 'Maybe'),
#     (AWAITING_FULL_TEXT, 'Awaiting Full Text'),
#     (EXCLUDED, 'Excluded'),
#     (FULL_TEXT_RECEIVED, 'Full Text Received' ),
# )
# review_status = models.CharField(
#     max_length=1,
#     choices=REVIEW_STATUS_CHOICES
# )

# events are unique unfortunately
class MaudeEvent(models.Model):
    searchId = models.ForeignKey(Search, on_delete=models.CASCADE)
    mdrReportKey = models.CharField(max_length=200, blank=False)
    eventUrl = models.CharField(max_length=400, blank=True)
    manufacturer = models.CharField(max_length=250, blank=False)
    eventDescription = models.CharField(max_length=8000, blank=False)
    product = models.CharField(max_length=250, blank=False)
    isRelevant = models.NullBooleanField(null=True, blank=True)


class ReviewerInput(models.Model):
    projectId = models.ForeignKey(Project, on_delete=models.CASCADE)
    deviceDescription = models.TextField(max_length=1000, null=True, blank=True)
    intendedUse = models.TextField(max_length=1000, null=True, blank=True)
    equivalentOverview = models.TextField(max_length=1000, null=True, blank=True)
    equivalentClinical = models.TextField(max_length=1000, null=True, blank=True)
    equivalentTechnical = models.TextField(max_length=1000, null=True, blank=True)
    equivalentBiological = models.TextField(max_length=1000, null=True, blank=True)


from django.contrib.postgres.fields import ArrayField

from s3direct.widgets import S3DirectWidget


class Device(models.Model):
    isEquivalent = models.NullBooleanField(null=True, blank=True)

    projectId = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True)

    deviceName = models.CharField(max_length=400, blank=True, null=True)
    manufacturer = models.CharField(max_length=400, blank=True, null=True)
    CEMarking = models.NullBooleanField(null=True, blank=True)

    clinicalPurpose = models.CharField(max_length=400, blank=True, null=True)
    intendedUse = models.TextField(max_length=400, blank=True, null=True)

    # enum of some kindg?
    patientPopulation = models.CharField(max_length=400, blank=True, null=True)

    anatomicalLocation = models.CharField(max_length=400, blank=True, null=True)
    intendedUser = models.CharField(max_length=400, blank=True, null=True)
    singleUse = models.BooleanField(blank=True, default=False)

    principalAction = models.TextField(max_length=400, blank=True, null=True)
    useConditions = models.CharField(max_length=400, blank=True, null=True)
    design = models.TextField(max_length=400, blank=True, null=True)
    specifications = models.TextField(max_length=400, blank=True, null=True)

    equivalentMaterials = models.CharField(max_length=400, blank=True, null=True)
    sterilization = models.CharField(max_length=400, blank=True, null=True)
    deviceImage = models.CharField(max_length=300, null=True, blank=True)


class ManufacturerIntake(models.Model):
    projectId = models.ForeignKey(Project, on_delete=models.CASCADE, editable=False)

    USFINT624 = 'USF624'
    REPORT_TYPE_CHOICES = ((USFINT624, 'FINT.624, Literature Review - US'), ("ITEM2", "ITem 2"))

    reportType = models.CharField(
        max_length=100, null=True, choices=REPORT_TYPE_CHOICES)

    productName = models.CharField(max_length=400, blank=True, null=True)
    productType = models.CharField(max_length=400, blank=True, null=True)

    equivalentDeviceList = ArrayField(models.CharField(max_length=150, blank=True), default=[], size=10, blank=True)
    equivalentDevice1 = models.CharField(max_length=100, null=True, blank=True)
    equivalentDevice2 = models.CharField(max_length=100, null=True, blank=True)
    equivalentDevice3 = models.CharField(max_length=100, null=True, blank=True)
    equivalentDevice4 = models.CharField(max_length=100, null=True, blank=True)
    equivalentDevice5 = models.CharField(max_length=100, null=True, blank=True)

    # THIS will be a query of Device WHERE projectId, isEquivalent=True

    # similars= unkown

    I = 'I'
    IIA = 'IIa'
    IIB = 'IIb'
    III = 'III'

    PRODUCT_CLASSIFICATION_CHOICES = (
    (I, 'EU Class I'), (IIA, 'EU Class IIA'), (IIB, 'EU Class IIB'), (III, 'EU Class III'))
    productClassification = models.CharField(max_length=4, blank=True, null=True,
                                             choices=PRODUCT_CLASSIFICATION_CHOICES)

    composition = models.CharField(max_length=400, blank=True, null=True)

    PMC = 'PMC'
    PUBMED = "PUB"
    COCHRANE = "COCHRANE"
    SCIENTIFIC_DB_CHOICES = ((PMC, "PMC"), (PUBMED, "PubMed"), (COCHRANE, "Cochrane"))
    # databasesScientific= ArrayField( models.NullBooleanField( choices=SCIENTIFIC_DB_CHOICES, null=True, blank=True) )
    databasesScientific_PMC = models.BooleanField(blank=True, default=False)
    databasesScientific_PUBMED = models.BooleanField(blank=True, default=False)
    databasesScientific_COCHRANE = models.BooleanField(blank=True, default=False)

    FDA = "FDA"
    SAFETY_DB_CHOICES = ((FDA, "FDA Maude Adverse Events"), ("EURODBSTUB", "Europe DB Stub"))

    # databasesSafety =  models.CharField(  max_length=15,  choices=SAFETY_DB_CHOICES)
    databaseSafety_FDA = models.BooleanField(blank=True, default=False)

    searchTerms = ArrayField(models.CharField(max_length=150, blank=True), null=True, blank=True)

    searchTermResultLimit = models.IntegerField(default=150)
    searchTermYears = models.IntegerField(default=10)

    # criteria is always the same.  populate on create submission.
    SEARCH_CRITERIA_DEFAULT = [
        'Human Studies',
        'Research Studies',
        'Reviews',
        'English-Only'
    ]

    INCLUSION_CRITERIA_DEFAULT = ['Risks', 'Performance', 'Safety', 'Similar IFU']

    EXCLUSION_CRITERIA_DEFAULT = [
        'Product mentioned but fails to address Performance, Risks, Safety, IFU or comparable product ',
        'Non-technical or technical animal results or cadavers ',
        'Unsubstantiated opinions',
        'Insufficient info to provide analysis',
        'Non-English or translation not available'
        ]

    searchCriteria = ArrayField(models.TextField(max_length=100), default=SEARCH_CRITERIA_DEFAULT, null=True,
                                blank=True)
    inclusionCriteria = ArrayField(models.CharField(max_length=100, blank=True), default=INCLUSION_CRITERIA_DEFAULT,
                                   null=True, blank=True)
    exclusionCriteria = ArrayField(models.CharField(max_length=100, blank=True), default=EXCLUSION_CRITERIA_DEFAULT,
                                   null=True, blank=True)

    technicalSheet = models.CharField(max_length=300, null=True, blank=True)








