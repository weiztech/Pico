# serializers.py
import os
import re
import csv
import io
import traceback
import datetime
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.files import File
import pandas as pd 
from backend.logger import logger
from rest_framework import serializers 
from lit_reviews.models import (
    LiteratureReview,
    LiteratureSearch,
    NCBIDatabase,   
    LiteratureReviewSearchProposal,
    ArticleReview,
)
from lit_reviews.database_imports.utils import parse_one_off_ris
from lit_reviews.helpers.generic import create_tmp_file
from lit_reviews.helpers.search_terms import get_search_date_ranges
from lit_reviews.tasks import generate_search_term_report
from lit_reviews.helpers.aws_s3 import generate_upload_presigned_url
from lit_reviews.helpers.articles import name_article_full_text_pdf

class NCBIDatabaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = NCBIDatabase
        fields = "__all__"


class LiteratureSearchSerializer(serializers.ModelSerializer):
    not_run_or_excluded = serializers.BooleanField()
    is_ae_not_maude = serializers.BooleanField()
    is_completed = serializers.BooleanField()
    none_excluded = serializers.BooleanField()
    limit_excluded = serializers.BooleanField()
    db = NCBIDatabaseSerializer()
    db_name = serializers.CharField(source="db.name")
    term_duplicates = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    maude_search_field = serializers.SerializerMethodField()
    completed_at = serializers.SerializerMethodField()

    def get_term_duplicates(self, obj):
        return len(
                ArticleReview.objects.filter(
                    search__id=obj.id, state="D"
                )
            )

    def get_start_date(self, obj):
        start_date, end_date = get_search_date_ranges(obj)
        if start_date:
            return start_date.strftime("%d-%m-%Y")
    
    def get_end_date(self, obj):
        start_date, end_date = get_search_date_ranges(obj)
        if end_date:
            return end_date.strftime("%d-%m-%Y")
    
    def get_maude_search_field(self, obj):
        return obj.advanced_options and obj.advanced_options.get("search_field", None)
    
    def get_completed_at(self, obj):
        return  obj.script_time.strftime("%m/%d/%Y") if obj.script_time else ""
    
    class Meta:
        model = LiteratureSearch
        fields = "__all__"


class UpdateLiteratureSearchSerializer(serializers.ModelSerializer):

    def validate_result_count(self, value):
        if value == None:
            raise serializers.ValidationError(f"Can't exclude a search without providing a result count, please Update result count value and try again!")
        if value < 0:
            raise serializers.ValidationError(f"Can't exclude a search with result count {value}, please Update result count value and try again!")

        return value 

    def update(self, instance, validated_data):
        validated_data["import_status"] = "COMPLETE"
        super().update(instance, validated_data)
        lit_review = LiteratureReview(id=instance.literature_review.id)
        lit_search_proposal = LiteratureReviewSearchProposal.objects.filter(
            literature_review=lit_review,
            db=instance.db,
            term=instance.term,
        ).first()
        if not lit_search_proposal:
           lit_search_proposal = LiteratureReviewSearchProposal.objects.create(
                literature_review=lit_review,
                db=instance.db,
                term=instance.term,
            ) 
        lit_search_proposal.result_count = validated_data["result_count"]
        lit_search_proposal.save()

        return instance 

    class Meta:
        model = LiteratureSearch
        fields = ["id", "result_count"]

class GenerateSearchReportSerializer(serializers.Serializer):
    search = serializers.IntegerField()

    def validate(self, data):
        search_id = data["search"]
        search = LiteratureSearch.objects.get(pk=search_id)
        data["search"] = search
        if search.import_status != "COMPLETE":
            raise serializers.ValidationError({
                "Search Term Report" : "This Search Term doesn't have a search file yet, Please either Run a manual or an Auto search first, Contact support for more help! "
            }) 

        return data

    def create(self, validated_data):
        search = validated_data["search"]
        search.search_report = None
        search.search_report_failing_msg = None
        search.save()
        generate_search_term_report.delay(search.id)
    
        return search
    

class RequestSupportHelpSerailizer(serializers.Serializer):
    CHOICES = [
        ('CALL', 'Call Me'),
        ('EMAIL', 'Email'),
        ('MEETING', 'Teams Meeting'),
    ]

    type = serializers.CharField()
    current_page = serializers.CharField(required=False, allow_blank=True) 
    message = serializers.CharField(required=False, allow_blank=True)
    demo_video = serializers.CharField(required=False, allow_blank=True)
    help_channels = serializers.MultipleChoiceField(choices=CHOICES,required=False)


    def validate(self, data):
        type = data.get('type')
        message = data.get('message')
        demo_video = data.get('demo_video')
        help_channels = data.get('help_channels')
        current_page = data.get("current_page")

        if type != "FULL_TEXT" and type != "RUN_SEARCH" and type != "SUPPORT_CALL" and type != "SUPPORT_TICKET":
            raise serializers.ValidationError("type should be either: 'FULL_TEXT' or 'RUN_SEARCH' or 'SUPPORT_CALL' or 'SUPPORT_TICKET'")
        if type == "SUPPORT_CALL" and not current_page:
            raise serializers.ValidationError("please provide us the link of current page ")
        if type == "SUPPORT_TICKET":
            error_messages = []
            if not message:
                error_messages.append("you missed 'How can we help?' field ")
            if not demo_video:
                error_messages.append("you missed 'Show us the issue' field ")
            if not help_channels:
                error_messages.append("you missed 'How Do You Want Us To Follow-Up?' field ")
            if len(error_messages) > 0:
                raise serializers.ValidationError(error_messages)


        return data 
    
    def create(self, validated_data):
        request = self.context.get("request")
        review = self.context.get("literature_review", None)
        
        if request.user.is_anonymous:
            username = "unkown"
            email = "unkown"
            
        else:
            user = request.user
            username = user.username
            email = user.email
            
        logger.info('username : {}', username)
        r_type = validated_data.get("type")
        if r_type == "FULL_TEXT":
            subject = "Client Request for uploading full text"
            message = f"""User {username} is experiencing difficulties with the full-text upload and is seeking assistance for project.
            <div>
                <div>
                    <b> Project Info </b> <br />
                    Device Name: {review.device} <br />
                    Project Link: {request.get_host()}/literature_reviews/{review.id}/full_text_upload <br />
                </div>
                <br />
                <div>
                    Client Name: {review.client} <br />
                    <b> User Info </b> <br />
                    Username: {username}  <br />
                    Email: {email}  <br />
                </div>
            </div>
            """
        elif r_type == "RUN_SEARCH":
            subject = "Client Request for running search terms"
            message = f"User with email {email} is experiencing difficulties with running searches for project: {str(review)}, and seeking assistance."
        elif r_type == "SUPPORT_CALL":
            current_page = validated_data.get("current_page")
            subject = "User Needs Help, Requesting Support Call"
            message = f"""
                User Email : {email} \n<br />
                User Username : {username} \n<br /> 
                Literature Review Project Name : {str(review)} \n<br /> 
                Page Requies Help : {request.get_host()+current_page}.
            """
        elif r_type == "SUPPORT_TICKET":
            current_page = validated_data.get("current_page")
            message = validated_data.get("message")
            demo_video = validated_data.get("demo_video")
            help_channels = validated_data.get("help_channels")
            help_channels = [dict(self.CHOICES).get(choice, choice) for choice in validated_data.get('help_channels', [])]
            subject = "User Needs Help"
            
            message = f"""
                User Email : {email} \n<br /> 
                User Username : {username} \n<br /> 
                Issue Description Message : {message} \n<br /> 
                Loom Demo Video : {demo_video}\n<br /> 
                He Want Us To Follow-up with Him Through : {' , '.join(help_channels)} \n<br />.
                Page Requies Help : {request.get_host()+current_page}.
            """


        return {"subject": subject, "message": message}

class UploadOwnCitationsSerializer(serializers.Serializer):
    database = serializers.CharField()
    file = serializers.FileField()
    external_db_name = serializers.CharField(required=False)
    external_db_url = serializers.CharField(required=False)

    def create(self, validated_data):
        db_name = validated_data.get("database")
        external_db_name = validated_data.get("external_db_name")
        external_db_url = validated_data.get("external_db_url")
        file = validated_data.get("file")

        if db_name == "external":
            db = NCBIDatabase.objects.filter(name=external_db_name, is_external=True).first()
            if not db:
                db = NCBIDatabase.objects.create(
                    name=external_db_name,
                    displayed_name=external_db_name,
                    is_archived=True,
                    is_external=True,
                    url=external_db_url,
                )
                
        else:
            db = NCBIDatabase.objects.get(name=db_name)

        literature_review = self.context.get("literature_review", None)
        tmp_file = create_tmp_file(file.name, file.read())
        search = LiteratureSearch.objects.get_or_create(
            literature_review = literature_review,
            term = "One-Off Manufacturer Search",
            db=db,
        )[0]
        results = parse_one_off_ris(tmp_file, literature_review.id, search.id)  

        if results["status"] == "COMPLETE":       
            return results
        else:
            count = results["count"]
            raise serializers.ValidationError(f"The file you've uploaded countains {count} results which exceeds the max you have set under the Search Protocol View")
        
class ValidateManualFileSearchSerializer(serializers.Serializer):
    manual_file = serializers.FileField()
    search_id = serializers.IntegerField()

    def validate(self,data):
        manual_file = data.get('manual_file')
        search_id = data.get('search_id')

        if manual_file:
            TMP_ROOT = settings.TMP_ROOT
            FILE_PATH = TMP_ROOT +  "/manual_files" + str(manual_file)
            with open(FILE_PATH, "wb") as f:
                for chunk in manual_file.chunks():
                    f.write(chunk)

            f = open(FILE_PATH, "r")
            manual_file_obj = File(f)
            manual_file_type = os.path.splitext(manual_file_obj.name)[1]
        else:
            raise serializers.ValidationError("The specified manual file does not exist.")
        
        validation = False
        validation_error = ""

        # Get the result file
        search = LiteratureSearch.objects.get(pk=search_id)
        result_file = search.search_file

        if result_file:
            result_file_type = os.path.splitext(result_file.name)[1]
            if result_file_type == manual_file_type:
                if result_file_type == '.txt' or result_file_type == ".ris":
                    with result_file.open(mode="r") as f1:
                        with open(FILE_PATH, "r") as f2:
                            validation = True
                            file1_content = f1.read()
                            file2_content = f2.read()

                            # Remove all white spaces from both files
                            file1_content = re.sub(r'\s', '', file1_content)
                            file2_content = re.sub(r'\s', '', file2_content)

                            # Split both files into lines
                            file1_lines = file1_content.split('\n')
                            file2_lines = file2_content.split('\n')

                            if len(file1_lines) != len(file2_lines):
                                validation_error = "Result files are not matching, either auto search generated wrong results or you didn't use the correct filters in your manual search please double check you're using the correct filters from search protocol page"
                                validation = False
                            else:
                                for i in range(len(file1_lines)):
                                    if file1_lines[i] != file2_lines[i]:
                                        validation_error = "Result files are not matching, either auto search generated wrong results or you didn't use the correct filters in your manual search please double check you're using the correct filters from search protocol page"
                                        validation = False
                                        break
                elif result_file_type == '.csv':
                    with result_file.open(mode="r") as f1:
                        with open(FILE_PATH, "r") as f2:
                            reader1 = csv.reader(io.StringIO(f1.read()))
                            reader2 = csv.reader(f2)
                            rows1 = []
                            rows2 = []
                            for row in reader1:
                                rows1.append(row)
                            for row in reader2:
                                rows2.append(row)
                            if len(rows1) != len(rows2):
                                validation_error = "Result files are not matching, either auto search generated wrong results or you didn't use the correct filters in your manual search please double check you're using the correct filters from search protocol page"
                                validation = False
                            else:
                                for i in range(len(rows1)):
                                    if rows1[i] != rows2[i]:
                                        validation_error = "Result files are not matching, either auto search generated wrong results or you didn't use the correct filters in your manual search please double check you're using the correct filters from search protocol page"
                                        validation = False
                                        break
                    
                                validation = True
                                
                elif result_file_type == '.xls':
                    # Compare two Excel files using pandas
                    try:
                        df1 = pd.read_excel(result_file)
                        df2 = pd.read_excel(FILE_PATH)

                        if not df1.equals(df2):
                            validation_error = "Result files are not matching, either auto search generated wrong results or you didn't use the correct filters in your manual search please double check you're using the correct filters from search protocol page"
                            validation = False
                        else:
                            validation = True
                    except Exception as e:
                        err_track = str(traceback.format_exc())
                        logger.error(f"Validating search terms failed due to the below error {str(err_track)}")
                        validation_error = str(e)
                        validation = False

            elif manual_file_type == ".csv" and result_file_type == ".xls" and search.db.entrez_enum == "maude":
                # Rename the manual file from .csv to .xls and compare the two xls
                manual_xls_file = FILE_PATH.replace(".csv", ".xls")
                os.rename(FILE_PATH, manual_xls_file)

                try:
                    df1 = pd.read_excel(result_file)
                    df2 = pd.read_excel(manual_xls_file)

                    if not df1.equals(df2):
                        validation_error = "Result files are not matching, either auto search generated wrong results or you didn't use the correct filters in your manual search please double-check you're using the correct filters from the search protocol page"
                        validation = False
                    else:
                        validation = True
                except Exception as e:
                    err_track = str(traceback.format_exc())
                    logger.error(f"Validating search terms failed due to the below error {str(err_track)}")
                    validation_error = str(e)
                    validation = False

            else:
                validation = False
                validation_error = "You Have Submitted a File With an Incorrect File Type. Please Upload a File of the Correct Type, Which is: "+ result_file_type
        else:
            validation = False
            validation_error = "The Search Term you Selected Has No Result File."

        return {
            "validation": validation,
            "validation_error": validation_error,
        }


class AWSDirectUploadSerializer(serializers.Serializer):
    TYPES = ["SEARCH", "FULL_TEXT_PDF"]

    type = serializers.ChoiceField(choices=TYPES)
    object_id =  serializers.IntegerField()
    file_format = serializers.CharField()


    def create(self, validated_data):
        if validated_data.get("type") == "SEARCH":
            search = LiteratureSearch.objects.get(id=validated_data.get("object_id"))
            simplified_term = re.sub('[^a-zA-Z ]','', search.term).replace(" ", "_")
            simplified_term = simplified_term if len(simplified_term) < 45 else simplified_term[:45]
            file_name = "uploads/files/{}-{}-{}.{}".format(
                simplified_term, 
                search.db, 
                str(datetime.datetime.now().timestamp()).replace(".", ""), 
                validated_data.get("file_format")
            )
            return generate_upload_presigned_url(file_name)

        elif validated_data.get("type") == "FULL_TEXT_PDF":
            object_id = validated_data.get("object_id")
            article_review = get_object_or_404(ArticleReview, pk=object_id)
            file_name = name_article_full_text_pdf(article_review.article)
            file_path = "uploads/files/{}".format(file_name)
            return generate_upload_presigned_url(file_path)