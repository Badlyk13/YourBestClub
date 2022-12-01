import secrets
import string

from django.contrib.auth.models import User
from director.models import Director, Trainer, Student, ClubGroup


def finding_user(user):
    try:
        find_user = user.director
        return find_user, 'director'
    except:
        try:
            find_user = user.trainer
            return find_user, 'trainer'
        except:
            find_user = user.student
            return find_user, 'student'


def finding_user_type(pk):
    try:
        find_user = Director.objects.get(pk=pk)
        return find_user, 'director'
    except:
        try:
            find_user = Trainer.objects.get(pk=pk)
            return find_user, 'trainer'
        except:
            find_user = Student.objects.get(pk=pk)
            return find_user, 'student'


def director_check(user):
    try:
        user = user.director
        return True
    except:
        return False


def trainer_check(user):
    try:
        user = user.trainer
        return True
    except:
        return False


def not_student_check(user):
    try:
        user = user.student
        return False
    except:
        return True


def generate_alphanum_crypt_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    crypt_rand_string = ''.join(secrets.choice(letters_and_digits) for i in range(length))
    return crypt_rand_string


