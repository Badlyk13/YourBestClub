from director.models import Director, Trainer, Student


def check_tg_id(tgID):
    find = Director.objects.filter(tgID=tgID)
    if not find:
        find = Trainer.objects.filter(tgID=tgID)
        if not find:
            find = Student.objects.filter(tgID=tgID)
            if not find:
                return True
        else:
            return False
    else:
        return False


def find_user_data(tgID):
    user_data = Director.objects.filter(tgID=tgID)
    if not user_data:
        user_data = Trainer.objects.filter(tgID=tgID)
        if not user_data:
            user_data = Student.objects.filter(tgID=tgID)
            if not user_data:
                return False
            else:
                user_type = 'student'
                return user_type, user_data
        else:
            user_type = 'trainer'
            return user_type, user_data
    else:
        user_type = 'director'
        return user_type, user_data