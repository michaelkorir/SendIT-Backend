# from flask_admin.contrib.sqla import  ModelView
# from models import User, Parcel

# class UserAdminView(ModelView):
#     column_sortable_list= ('username', 'email','role')
#     column_searchable_list=('username','email','role')
#     column_list=('username','email','role')
#     column_labels=dict(username='Username', email='Email', role='Role')
#     column_filters=column_list

# class ParcelAdminView(ModelView):
#     column_sortable_list= ('name', 'created_at', 'weight','pickup_location', 'destination_location','status','updated_at')
#     column_searchable_list=column_sortable_list
#     column_list=('name','description','tracking_number','weight','pickup_location','destination_location','status','created_at','updated_at')
#     column_labels=dict(name='Parcel Name', weight='Weight (kg)', tracking_number='Tracking Number',pickup_location='Pickup',status='Status')
#     column_filters=column_list