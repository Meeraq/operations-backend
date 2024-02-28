from rest_framework.permissions import BasePermission


class IsPmo(BasePermission):
    def has_permission(self, request, view):
        return request.user.profile.roles.filter(name="pmo").exists()


class IsCoach(BasePermission):
    def has_permission(self, request, view):
        return request.user.profile.roles.filter(name="coach").exists()


class IsLearner(BasePermission):
    def has_permission(self, request, view):
        return request.user.profile.roles.filter(name="learner").exists()


class IsHr(BasePermission):
    def has_permission(self, request, view):
        return request.user.profile.roles.filter(name="hr").exists()


class IsVendor(BasePermission):
    def has_permission(self, request, view):
        return request.user.profile.roles.filter(name="hr").exists()


class IsInRoles(BasePermission):
    def __init__(self, *roles):
        self.roles = roles

    def has_permission(self, request, view):
        return request.user.profile.roles.filter(name__in=self.roles).exists()


IsPmoAndCoach = IsInRoles("PMO", "COACH")
