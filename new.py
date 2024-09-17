from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import View
from .models import (
    Orders, Comments, Ordercomresponsible, CustomersList,
    Orderresponsible, Costs, Approvedlists, Favorites
)
from datetime import date


class OrderList(LoginRequiredMixin, View):
    def get(self, request):
        orders = Orders.objects.all()
        search_params = request.user.search  # Предполагается, что у пользователя есть связанные параметры поиска
        filters = Q()

        if search_params.search:
            filters &= Q(name__icontains=search_params.search) | Q(searchowners__icontains=search_params.search)
        else:
            if search_params.goal:
                filters &= Q(goal=True)
            if search_params.favorite:
                favorite_orders = Favorites.objects.filter(user=request.user).values_list('order__orderid', flat=True)
                filters &= Q(orderid__in=list(favorite_orders))
            if search_params.manager:
                responsible_orders = Orderresponsible.objects.filter(user=search_params.manager).values_list('orderid__orderid', flat=True)
                com_responsible_orders = Ordercomresponsible.objects.filter(
                    user=search_params.manager
                ).exclude(orderid__orderid__in=responsible_orders).values_list('orderid__orderid', flat=True)
                all_responsible_orders = set(responsible_orders).union(com_responsible_orders)
                filters &= Q(orderid__in=all_responsible_orders)
            if search_params.stage:
                filters &= Q(stageid=search_params.stage)
            if search_params.company:
                filters &= Q(cityid__isnull=True) | Q(cityid=search_params.company)
            if search_params.customer:
                filters &= Q(searchowners__icontains=search_params.customer)

        orders = orders.filter(filters)

        if request.GET.get('action') == 'count':
            return JsonResponse({'count': orders.count()})

        start = int(request.GET.get('start', 0))
        stop = int(request.GET.get('stop', 10))
        orders = orders.order_by('-reiting')[start:stop]

        orders = orders.prefetch_related(
            'customerslist_set__customerid',
            'comments_set',
            'orderresponsible_set',
            'favorites_set'
        )

        context_orders = []
        today = date.today()

        for order in orders:
            customers = order.customerslist_set.all().order_by('customerid__title')
            last_comment = order.comments_set.order_by('-createdat').first()
            last_contact = last_comment.createdat if last_comment else ''
            task_count = order.comments_set.filter(istask=True).exclude(complete=True).count()
            is_favorite = order.favorites_set.filter(user=request.user).exists()
            responsibles = order.orderresponsible_set.all()

            context_orders.append({
                'order': order,
                'customers': customers,
                'is_favorite': is_favorite,
                'last_contact': last_contact,
                'task_count': task_count,
                'responsibles': responsibles
            })

        context = {
            'orders': context_orders,
            'Today': today
        }
        return render(request, 'main/orders_list.html', context)


class CostList(LoginRequiredMixin, View):
    def get(self, request):
        costs = Costs.objects.all()
        search_params = request.user.search
        filters = Q()

        if search_params.search:
            filters &= (
                Q(description__icontains=search_params.search) |
                Q(section__icontains=search_params.search) |
                Q(orderid__name__icontains=search_params.search)
            )
        else:
            if search_params.goal:
                filters &= Q(orderid__goal=True)
            if search_params.favorite:
                favorite_orders = Favorites.objects.filter(user=request.user).values_list('order__orderid', flat=True)
                filters &= Q(orderid__in=list(favorite_orders))
            if search_params.manager:
                filters &= Q(user=search_params.manager)
            if search_params.stage:
                filters &= Q(orderid__stageid=search_params.stage)
            if search_params.company:
                filters &= Q(orderid__cityid__isnull=True) | Q(orderid__cityid=search_params.company)
            if search_params.customer:
                filters &= Q(orderid__searchowners__icontains=search_params.customer)

        costs = costs.filter(filters)

        if request.GET.get('action') == 'count':
            return JsonResponse({'count': costs.count()})

        start = int(request.GET.get('start', 0))
        stop = int(request.GET.get('stop', 10))
        costs = costs.order_by('-createdat')[start:stop]

        costs = costs.prefetch_related('approvedlists_set')

        context_costs = []
        today = date.today()

        for cost in costs:
            approvals = cost.approvedlists_set.all()
            context_costs.append({
                'cost': cost,
                'approvals': approvals
            })

        context = {
            'costs': context_costs,
            'Today': today
        }
        return render(request, 'main/cost_list.html', context)
