# Iniciating Redis client
import redis
import multiprocessing
r = redis.Redis(host='localhost', port=6379, db=2)

#--------------------------------------------------------------#
def create_session(session_id, Date, Time, Film_name):
    # Checks if session exists
    if r.exists(f"session:{session_id}"):
        return "session is already exists"
    
    # Creating new session
    session = {
        "Date": Date,
        "Time": Time,
        "Film_name": Film_name,
    }
    
    # Saving session in Redis
    r.hmset(f"session:{session_id}", session)
    return "Session is created"
#--------------------------------------------------------------#
def assign_seats_to_sessions():
    # Get sessions's keys
    session_keys = r.keys("session:*")

    # Check if there is sessions
    if not session_keys:
        print("No sessions found.")
        return

    # Rows and seats
    num_rows = 5
    num_seats_per_row = 20

    # Session with theater which has 100 seats with 5 rows
    for key in session_keys:
        print(key)
        session_id = key.decode('utf-8')
        print(session_id)
        sorted_set_key = f"Free_seats:{session_id}"

        #Patikrinkime, ar jau priskirta vietų
        if r.exists(sorted_set_key):
            print(f"Seats already assigned for session {session_id}")
            continue

        g=10
        # Assign seats
        for letter in range(ord('A'), ord('E') + 1):
            for seat in range(1,21):
                # Seats with letters and numbers
                seat_number = f"{chr(letter)}{seat}"
                score = g + seat
                r.zadd(sorted_set_key, {seat_number: score})
            g=g*10
        
        
        print(f"Assigned {num_rows * num_seats_per_row} seats for session {session_id}")

#-----------------------------------------------------------------------#
def print_all_sessions():

    # Get sessions's key
    session_keys = r.keys("session:*")

    # Check if there is keys
    if not session_keys:
        print("No sessions found.")
        return

    # Print sessions
    for key in session_keys:
        session_data = r.hgetall(key)

        print(f"Session ID: {key.decode('utf-8')}")
        for field, value in session_data.items():
            print(f"{field.decode('utf-8')}: {value.decode('utf-8')}")
        print("----------------------")
#-----------------------------------------------------------------------#

def print_seats(session_id):

    # Rows and seats
    num_rows = 5
    num_seats_per_row = 20

    sorted_set_key = f"Free_seats:session:{session_id}"
            
    # Get the seats from sorted set
    seats = r.zrange(sorted_set_key, 0, -1, withscores=True)

    if seats:
        for seat, seat_info in enumerate(seats, start=1):
            seat_number, score = seat_info
            print(f"{seat_number.decode('utf-8')}", end=" ")

            # Check if 20 seats was printed and print new line
            if seat % num_seats_per_row == 0:
                print()  # New line
    else:
        print("No seats found.")

def move_seat(session_id, member):
    free_seats_key = f"Free_seats:session:{session_id}"
    occupied_seats_key = f"Occupied_seats:session:{session_id}"

    # Begin the transaction
    with r.pipeline() as pipe:
        while True:
            try:
                # Watch the free_seats_key
                pipe.watch(free_seats_key)
                print("Pause")
                input()
                current_free_seats = pipe.zrange(free_seats_key, 0, -1)
                # Check if the member is in Free_seats
                if member.encode('utf-8') in current_free_seats:
                    # Begin the transaction
                    pipe.multi()

                    # Remove the member from Free_seats
                    pipe.zrem(free_seats_key, member)

                    # Add the member to Occupied_seats with the same score
                    score = r.zscore(free_seats_key, member)
                    pipe.zadd(occupied_seats_key, {member: score})

                    # Execute the transaction
                    pipe.execute()

                    print(f"Seat {member} moved from Free_seats to Occupied_seats.")
                    return True
                else:
                    print(f"Seat {member} not found in Free_seats or already in Occupied_seats.")
                    return False

            except redis.WatchError:
                continue
# main
if __name__ == '__main__':
    
    success_seassion = True
    success_book = True
    success_seat = True
    Checking = True

#---------------sessions are created------------------
    create_session("S1", "2023-11-25", "15:00", "Mike Pukuotukas") #Session is created
    create_session("S2", "2023-11-11", "22:30", "Kietas Riesutelis") #Session is created
    create_session("S3", "2023-11-12", "12:00", "Srekas") #Session is created

#-----------------Seats are assigned---------------------------------
    assign_seats_to_sessions()


    print("Session:")
    print_all_sessions()

#---Session Loop----------------------------------------#
    while (success_seassion):
        booksession_user = input("Select the session: ")
        booksession = booksession_user.upper()
    #---Session is choosed--------------------------->
        if r.exists(F"session:{booksession}"):
            print("Selected session: " + booksession)
            print('Session seats: ')
            print_seats(booksession)
        #----Booking the seat------------------------>
            success_seassion = False
        else:
            print("Session does not exits")
    
#-------------Seat Loop----------------------------------------------#
    while(success_book):
        while (success_seat):
            print(end = "\n")
            bookseat_user = input("Select the seat: ")
            bookseat = bookseat_user.upper()
            
            #---Seats is choosed----s----------------------->
            #rank = r.zrank(f"Free_seats:session:{booksession}", bookseat)

            #if rank is not None:
            Checking = move_seat(booksession, bookseat)
            if Checking:
                #----Booking the seat------------------------>
                print("Booked seat: " + bookseat)
                success_seat = False
            else:
                    print('Seat unavailable')
                    print('Remaining free seats: ')
                    print_seats(booksession)
        #----Booking another seat------------------------>
        continue_book_user = input("Book another ticket? [Y/N] ")
        continue_book = continue_book_user.upper()
        if continue_book == 'N':
            success_book = False
        elif continue_book == 'Y':
            success_seat = True
