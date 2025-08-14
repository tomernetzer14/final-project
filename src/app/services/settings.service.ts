import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SettingsService {
  private langSubject = new BehaviorSubject<string>('he');
  lang$ = this.langSubject.asObservable();

  setLang(lang: string) {
    this.langSubject.next(lang);
  }

  getCurrentLang(): string {
    return this.langSubject.getValue();
  }

  private advancedModeSubject = new BehaviorSubject<'basic' | 'advanced'>('basic');
  advancedMode$ = this.advancedModeSubject.asObservable();

  setAdvancedMode(mode: 'basic' | 'advanced') {
    this.advancedModeSubject.next(mode);
  }

  getCurrentMode(): 'basic' | 'advanced' {
    return this.advancedModeSubject.getValue();
  }

}
