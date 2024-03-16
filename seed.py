from models import db, User, Parcel
from app import app

def seed_data():
    with app.app_context():
        
        # Delete existing data
        db.session.query(User).delete()
        db.session.query(Parcel).delete()

        users = [
            {'username': 'user1', 'email': 'michael.kiptoo@student.moringaschool.com', 'password': 'password1'},
            {'username': 'user2', 'email': 'ian.kiplagat@student.moringaschool.com', 'password': 'password2'},
            {'username': 'user3', 'email': 'mueni.shikuku@student.moringaschool.com', 'password': 'password3'},
            {'username': 'user4', 'email': 'allan.murigi@student.moringaschool.com', 'password': 'password4'},
            {'username': 'user5', 'email': 'masud.abdi@student.moringaschool.com', 'password': 'password5'},
            {'username': 'admin1', 'email': 'admin1@example.com', 'password': 'admin1', 'role': 'admin'}
        ]

        for data in users:
            # Check if the role is specified, default to 'user'
            role = data.get('role', 'user')

            # Create the user
            user = User(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                role=role
            )
            db.session.add(user)

        # Commit the changes to the database
        db.session.commit()
        print("Users created successfully")

        parcels_data = [
            {'user_id': 1, 'name': 'laptop', 'description': 'Hp Laptop in a box', 'weight': 2.5, 'pickup_location': 'Nairobi', 'destination_location': 'Mombasa', 'status': 'pending', 'present_location': 'Nairobi', 'notifications': 'Your parcel has been picked up and is on its way to Mombasa.'},
            {'user_id': 2, 'name': 'laptop', 'description': 'Hp Laptop in a box', 'weight': 1.8, 'pickup_location': 'Kisumu', 'destination_location': 'Nakuru', 'status': 'pending', 'present_location': 'Kisumu', 'notifications': 'Your parcel has been picked up and is on its way to Nakuru.'},
            {'user_id': 3, 'name': 'laptop', 'description': 'Hp Laptop in a box', 'weight': 3.2, 'pickup_location': 'Eldoret', 'destination_location': 'Nairobi', 'status': 'in-transit', 'present_location': 'Eldoret', 'notifications': 'Your parcel has been picked up and is on its way to Nairobi.'},
            {'user_id': 4, 'name': 'laptop', 'description': 'Hp Laptop in a box', 'weight': 0.9, 'pickup_location': 'Mombasa', 'destination_location': 'Kisumu', 'status': 'delivered', 'present_location': 'Kisumu', 'notifications': 'Your parcel has been delivered to Kisumu.Visit our office to collect your parcel.'},
            {'user_id': 5, 'name': 'laptop', 'description': 'Hp Laptop in a box', 'weight': 0.9, 'pickup_location': 'Mombasa', 'destination_location': 'Kisumu', 'status': 'delivered', 'present_location': 'Kisumu', 'notifications': 'Your parcel has been delivered to Kisumu.Visit our office to collect your parcel.'}
        ]

        parcels = []
        for parcel_data in parcels_data:
            new_parcel = Parcel(
                user_id=parcel_data['user_id'],
                name=parcel_data['name'],
                description=parcel_data['description'],
                weight=parcel_data['weight'],
                pickup_location=parcel_data['pickup_location'],
                destination_location=parcel_data['destination_location'],
                status=parcel_data['status'],
                present_location=parcel_data['present_location'],
                notifications=parcel_data['notifications']
            )
            parcels.append(new_parcel)

        db.session.add_all(parcels)
        db.session.commit()
        print("Parcels created successfully")

if __name__ == '__main__':
    seed_data()