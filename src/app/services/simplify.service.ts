import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Metrics } from './api.service';


@Injectable({
  providedIn: 'root'
})
export class SimplifyService {
  private simplifiedTextSource = new BehaviorSubject<string>('');
  simplifiedText$ = this.simplifiedTextSource.asObservable();

  private simplifiedActiveSource = new BehaviorSubject<boolean>(false);
  simplifiedActive$ = this.simplifiedActiveSource.asObservable();

  private keywordsSource = new BehaviorSubject<{ [section: string]: string[] }>({});
  keywords$ = this.keywordsSource.asObservable();

  private baselineTextSource = new BehaviorSubject<string>('');
  baselineText$ = this.baselineTextSource.asObservable();

  private traceSource = new BehaviorSubject<any>(null);
  trace$ = this.traceSource.asObservable();

  private metricsSource = new BehaviorSubject<Metrics | null>(null);
  metrics$ = this.metricsSource.asObservable();

  setMetrics(metrics: Metrics  | null) {
  this.metricsSource.next(metrics);
}
  setTrace(trace: any) {
    this.traceSource.next(trace);
  }

  setSimplifiedText(text: string) {
    this.simplifiedTextSource.next(text);
    this.simplifiedActiveSource.next(!!text);
  }

  setKeywords(keywords: { [section: string]: string[] }) {
    this.keywordsSource.next(keywords);
  }

  setBaselineText(text: string) {
  this.baselineTextSource.next(text);
  } 

  clear() {
    this.simplifiedTextSource.next('');
    this.simplifiedActiveSource.next(false);
    this.keywordsSource.next({});
    this.baselineTextSource.next('');
    this.traceSource.next(null);
    this.metricsSource.next(null);


  }
}
