class CustomAPIException(Exception):
    status_code = None

    def __int__(self, errors):
        super(CustomAPIException, self).__init__()
        self.errors = errors
        self.detail = errors

    def get_full_details(self):
        return self.errors

class ServiceValidationError(CustomAPIException):
    status_code = 400
