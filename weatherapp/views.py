from django.shortcuts import render, get_object_or_404, redirect
from decouple import config
import requests
from django.contrib import messages
from .models import City
from users.models import UserProfile

# Hava durumu verilerini almak için yardımcı fonksiyon
def get_weather_data(city_name, api_key):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city_name}&lang=tr&appid={api_key}&units=metric'
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.json()
        return {
            'city': city_name,
            'temp': content['main']['temp'],
            'icon': content['weather'][0]['icon'],
            'desc': content['weather'][0]['description'],
        }
    except requests.exceptions.RequestException:
        return None

# Yeni bir şehir eklemek için kullanıcıya özel kontrol yapan fonksiyon
def add_city(city_name, user):
    # Yalnızca bu kullanıcıya ait şehirlerin isimlerini kontrol ediyoruz
    user_cities = City.objects.filter(name=city_name, user=user)
    if user_cities.exists():
        return False
    new_city = City.objects.create(name=city_name)
    new_city.user.add(user)
    return True

# Ana görünüm
def index(request):
    API_KEY = config('API_KEY')
    user = request.user
    city_data = []
    profile = None
    
    # Kullanıcıya ait profilin var olup olmadığını kontrol etme
    if user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=user)

    # Yeni şehir ekleme işlemi
    u_city = request.POST.get('name')
    if u_city:
        if get_weather_data(u_city, API_KEY):
            if add_city(u_city, user):
                messages.success(request, 'Şehir eklendi.')
            else:
                messages.warning(request, 'Bu şehir zaten listenizde mevcut!')
        else:
            messages.warning(request, 'Böyle bir şehir bulunamadı.')

    # Superuser için tüm şehirleri gösterme, diğer kullanıcılar için yalnızca kendi şehirlerini
    if user.is_authenticated:
        if user.is_superuser:
            cities = City.objects.all().order_by('-id')
        else:
            cities = City.objects.filter(user=user).order_by('-id')
        
        # Şehirlerin hava durumu verilerini alıp listeye ekleme
        for city in cities:
            data = get_weather_data(city.name, API_KEY)
            if data:
                data['city'] = city
                city_data.append(data)

    # Context ve render işlemi
    context = {
        'city_data': city_data,
        'profile': profile,
    }
    return render(request, 'weatherapp/index.html', context)

# Şehir silme işlemi
def delete_city(request, id):
    city = get_object_or_404(City, id=id, user=request.user)  # Sadece bu kullanıcının şehirlerini silme
    city.delete()
    messages.warning(request, 'Şehir silindi.')
    return redirect('weatherapp:home')
