import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';

interface User {
  username: string;
  email?: string;
  full_name?: string;
  role: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject: BehaviorSubject<User | null>;
  public currentUser: Observable<User | null>;
  private apiUrl = 'http://localhost:8000';

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    const user = localStorage.getItem('currentUser');
    this.currentUserSubject = new BehaviorSubject<User | null>(user ? JSON.parse(user) : null);
    this.currentUser = this.currentUserSubject.asObservable();
  }

  public get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  login(username: string, password: string): Observable<User> {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    return this.http.post<LoginResponse>(`${this.apiUrl}/token`, formData)
      .pipe(
        map(response => {
          localStorage.setItem('access_token', response.access_token);
          
          // Decode JWT to get user info
          const tokenParts = response.access_token.split('.');
          const tokenPayload = JSON.parse(atob(tokenParts[1]));
          
          const user: User = {
            username: tokenPayload.sub,
            role: 'user' // Default role, will be updated after profile fetch
          };
          
          localStorage.setItem('currentUser', JSON.stringify(user));
          this.currentUserSubject.next(user);
          
          // Fetch user profile
          this.getUserProfile().subscribe(profile => {
            localStorage.setItem('currentUser', JSON.stringify(profile));
            this.currentUserSubject.next(profile);
          });
          
          return user;
        })
      );
  }

  getUserProfile(): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/users/me/`);
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('currentUser');
    this.currentUserSubject.next(null);
    this.router.navigate(['/login']);
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  isAdmin(): boolean {
    const user = this.currentUserValue;
    return user?.role === 'admin';
  }
}
