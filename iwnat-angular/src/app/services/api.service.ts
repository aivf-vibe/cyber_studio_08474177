

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

interface Service {
  id: number;
  name: string;
  description: string;
  icon: string;
  features: string[];
}

interface Product {
  id: number;
  name: string;
  description: string;
  features: string[];
  image_url?: string;
}

interface ContactMessage {
  name: string;
  email: string;
  company: string;
  message: string;
}

interface User {
  username: string;
  email?: string;
  full_name?: string;
  role: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  getServices(): Observable<Service[]> {
    return this.http.get<Service[]>(`${this.apiUrl}/api/services`);
  }

  getService(id: number): Observable<Service> {
    return this.http.get<Service>(`${this.apiUrl}/api/services/${id}`);
  }

  getProducts(): Observable<Product[]> {
    return this.http.get<Product[]>(`${this.apiUrl}/api/products`);
  }

  getProduct(id: number): Observable<Product> {
    return this.http.get<Product>(`${this.apiUrl}/api/products/${id}`);
  }

  sendContactMessage(message: ContactMessage): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/contact`, message);
  }

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${this.apiUrl}/api/admin/users`);
  }

  createUser(user: any): Observable<User> {
    return this.http.post<User>(`${this.apiUrl}/api/admin/users`, user);
  }
}

