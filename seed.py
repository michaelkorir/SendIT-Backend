from models import db, User, Parcel
from app import app

def seed_data():
    with app.app_context():
        
        # Delete existing data
        db.session.query(User).delete()
        db.session.query(Parcel).delete()

        users = [
            {'username': 'Michael', 'email': 'michael.kiptoo@student.moringaschool.com', 'password': '123456'},
            {'username': 'Ian', 'email': 'ian.kiplagat@student.moringaschool.com', 'password': '123456'},
            {'username': 'Mueni', 'email': 'mueni.shikuku@student.moringaschool.com', 'password': '123456'},
            {'username': 'Allan', 'email': 'allan.murigi@student.moringaschool.com', 'password': '123456'},
            {'username': 'Masud', 'email': 'masud.abdi@student.moringaschool.com', 'password': '123456'},
            {'username': 'admin', 'email': 'admin1@example.com', 'password': 'admin1', 'role': 'admin'}
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
            {'user_id': 1, 'name': 'Laptop', 'description': 'Hp Laptop in a box', 'weight': 2.5, 'pickup_location': 'Nairobi', 'destination_location': 'Mombasa', 'status': 'pending', 'present_location': 'Nairobi'},
            {'user_id': 2, 'name': 'Laptop', 'description': 'Hp Laptop in a box', 'weight': 1.8, 'pickup_location': 'Kisumu', 'destination_location': 'Nakuru', 'status': 'pending', 'present_location': 'Kisumu'},
            {'user_id': 3, 'name': 'Laptop', 'description': 'Hp Laptop in a box', 'weight': 3.2, 'pickup_location': 'Eldoret', 'destination_location': 'Nairobi', 'status': 'in-transit', 'present_location': 'Eldoret'},
            {'user_id': 4, 'name': 'Laptop', 'description': 'Hp Laptop in a box', 'weight': 0.9, 'pickup_location': 'Mombasa', 'destination_location': 'Kisumu', 'status': 'delivered', 'present_location': 'Kisumu'},
            {'user_id': 5, 'name': 'Laptop', 'description': 'Hp Laptop in a box', 'weight': 0.9, 'pickup_location': 'Mombasa', 'destination_location': 'Kisumu', 'status': 'delivered', 'present_location': 'Kisumu'}
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
                present_location=parcel_data['present_location']
            )
            parcels.append(new_parcel)

        db.session.add_all(parcels)
        db.session.commit()
        print("Parcels created successfully")

if __name__ == '__main__':
    seed_data()