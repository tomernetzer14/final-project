import { Component, OnInit } from '@angular/core';
import { SettingsService } from '../../services/settings.service';
import { SimplifyService } from '../../services/simplify.service';

@Component({
  selector: 'app-language-selector',
  standalone: false,
  templateUrl: './language-selector.component.html',
  styleUrl: './language-selector.component.css'
})
export class LanguageSelectorComponent implements OnInit {
  selectedLanguage: string = 'he';
  selectedAdvanced: 'basic' | 'advanced' = 'basic';
  hide = false;

  constructor(
    private simplifyService: SimplifyService,
    private settingsService: SettingsService
  ) {}

  ngOnInit() {
    this.simplifyService.simplifiedActive$.subscribe((active) => {
      //this.hide = active;
    });

    this.settingsService.setAdvancedMode(this.selectedAdvanced);
  }

  onModeChange() {
    this.settingsService.setAdvancedMode(this.selectedAdvanced);
  }
  
  ngDoCheck() {
    this.settingsService.setLang(this.selectedLanguage);
  }
}



