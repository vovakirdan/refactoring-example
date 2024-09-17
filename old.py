from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from .models import Orders, Comments, Ordercomresponsible, CustomersList, Customer, Orderresponsible
from .models import Costs, Approvedlists, Favorites
from datetime import *
from django.views.generic import View


class OrderList(LoginRequiredMixin, View):
    def get(self, request):
        orders = Orders.objects.all()
        if request.user.search.search is not None and request.user.search.search != '':
            orders = orders.filter(
                Q(name__icontains=request.user.search.search) | Q(searchowners__icontains=request.user.search.search))
        else:
            if request.user.search.goal:
                orders = orders.filter(goal=True)

            if request.user.search.favorite:
                fav = Favorites.objects.filter(user=request.user)
                orders_fav = []
                for i in fav:
                    orders_fav.append(i.order.orderid)
                orders = orders.filter(orderid__in=orders_fav)
            if request.user.search.manager is not None:
                res = Orderresponsible.objects.filter(user=request.user.search.manager)
                order_res = []
                for i in res:
                    order_res.append(i.orderid.orderid)
                res = Ordercomresponsible.objects.filter(user=request.user.search.manager)
                res = res.exclude(orderid__orderid__in=order_res)
                for i in res:
                    order_res.append(i.orderid.orderid)
                orders = orders.filter(orderid__in=order_res)
            if request.user.search.stage is not None:
                orders = orders.filter(stageid=request.user.search.stage)
            if request.user.search.company is not None:
                orders = orders.filter(Q(cityid=None) | Q(cityid=request.user.search.company))
            if request.user.search.customer != '':
                orders = orders.filter(searchowners__icontains=request.user.search.customer)
        if request.GET['action'] == 'count':
            return JsonResponse({'count': orders.count()})
        orders = orders.order_by('-reiting')[int(request.GET['start']):int(request.GET['stop'])]
        customers = []
        lastcontact = []
        resp = []
        favorite = []
        task = []
        for i in orders:
            resp.append(Orderresponsible.objects.filter(orderid=i.orderid))
            customerslist = CustomersList.objects.filter(orderid=i.orderid).order_by('customerid__title')
            customers.append(customerslist)
            if Comments.objects.filter(orderid=i).count() == 0:
                lastcontact.append('')
            else:
                lastcontact.append(Comments.objects.filter(orderid=i)[0].createdat)
            task.append(Comments.objects.filter(orderid=i).filter(istask=1).exclude(complete=1).count())

            if Favorites.objects.filter(user=request.user).filter(order=i).count() == 0:
                favorite.append(False)
            else:
                favorite.append(True)
        context = {
            'orders': zip(orders, customers, favorite, lastcontact, task, resp),
            'Today': date.today()
        }
        return render(request, 'main/orders_list.html', context)


class CostList(LoginRequiredMixin, View):
    def get(self, request):
        costs = Costs.objects.all()
        if request.user.search.search is not None and request.user.search.search != '':
            costs = costs.filter(
                Q(description__icontains=request.user.search.search) | Q(
                    section__icontains=request.user.search.search) | Q(
                    orderid__name__icontains=request.user.search.search))
        else:
            if request.user.search.goal is True:
                costs = costs.filter(orderid__goal=True)
            if request.user.search.favorite is True:
                fav = Favorites.objects.filter(user=request.user)
                orders_fav=[]
                for i in fav :
                    orders_fav.append(i.order.orderid)
                costs = costs.filter(orderid__in=orders_fav)
            if request.user.search.manager is not None :
                costs = costs.filter(user=request.user.search.manager)
            if request.user.search.stage is not None:
                costs = costs.filter(orderid__stageid=request.user.search.stage)
            if request.user.search.company is not None:
                costs = costs.filter(Q(orderid__cityid=None) | Q(orderid__cityid=request.user.search.company))
            if request.user.search.customer != '':
                costs = costs.filter(orderid__searchowners__icontains=request.user.search.customer)
        if request.GET['action'] == 'count':
            return JsonResponse({'count':costs.count()})
        costs = costs.order_by('-createdat')[int(request.GET['start']):int(request.GET['stop'])]
        appr=[]
        for i in costs:
            appr.append(Approvedlists.objects.filter(cost_id=i))
        context = {
            'costs': zip(costs, appr),
            'Today': date.today()
        }
        return render(request, 'main/cost_list.html', context)