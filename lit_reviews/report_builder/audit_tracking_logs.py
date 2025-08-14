from backend.logger import logger
from actstream.models import Action
from django.utils import timezone
from django.urls import reverse

def audit_tracking_logs_context(lit_review_id):

    row_list = []
    header = ["User", "Date & Time", "Action Type","Description","Link to Action"]
    row_list.append(header)
    
    try:
        actions = Action.objects.filter(
                target_object_id=lit_review_id,
                public = True
            ).order_by('-timestamp')

        
        for action in actions:
            row=[]
            # add user (username)
            row.append(action.actor.username if action.actor else 'Unknown')
            # add data and time
            row.append(timezone.localtime(action.timestamp).strftime('%Y-%m-%d %H:%M:%S'))
            # add action type (verb)
            row.append(action.verb)
            # add action description
            row.append(action.description)
            # add action object link 
            row.append(action.action_object.get_absolute_url() if action.action_object and hasattr(action.action_object, 'get_absolute_url') else 'N/A')

            row_list.append(row)

        return row_list

    except Exception as e:
        logger.error("Error: {0}".format(str(e)))
        return row_list