import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Metrics {
  readability: number;
  complexity: number;
  frequencyScore: number;
  bert: number;
  berts: number
}

export interface SimplifyResponse {
  original: string;
  simplified: string;
  keywords: { [section: string]: string[] };
  baseline: string; 
  trace: any;
  metrics: Metrics;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:5001';

  constructor(private http: HttpClient) {}

  simplifyText(text: string): Observable<SimplifyResponse> {
    return this.http.post<SimplifyResponse>(`${this.baseUrl}/simplify`, { text });
  }

  extractPdf(file: File): Observable<string> {
    const formData = new FormData();
    formData.append('input', file, file.name);
  
    return this.http.post(`${this.baseUrl}/extract-pdf`, formData, {
      responseType: 'text'
    });
  }


}
