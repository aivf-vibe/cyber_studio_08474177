



import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';

interface User {
  username: string;
  email?: string;
  full_name?: string;
  role: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8000';
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser = this.currentUserSubject.asObservable();

  constructor(private http: HttpClient) {
    const token = localStorage.getItem('token');
    if (token) {
      this.getCurrentUser().subscribe();
    }
  }

  login(username: string, password: string): Observable<User> {
    return this.http.post<any>(`${this.apiUrl}/token`, { username, password })
      .pipe(
        map(response => {
          localStorage.setItem('token', response.access_token);
          const user = response.user;
          this.currentUserSubject.next(user);
          return user;
        })
      );
  }

  logout() {
    localStorage.removeItem('token');
    this.currentUserSubject.next(null);
  }

  getCurrentUser(): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/users/me/`)
      .pipe(
        map(user => {
          this.currentUserSubject.next(user);
          return user;
        })
      );
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem('token');
  }

  isAdmin(): boolean {
    const user = this.currentUserSubject.value;
    return user?.role === 'admin';
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }
}



