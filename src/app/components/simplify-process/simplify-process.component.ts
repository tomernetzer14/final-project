import { Component, OnInit } from '@angular/core';
import { SimplifyService } from '../../services/simplify.service';
import { SettingsService } from '../../services/settings.service';

@Component({
  selector: 'app-simplify-process',
  standalone: false,
  templateUrl: './simplify-process.component.html',
  styleUrl: './simplify-process.component.css'
})
export class SimplifyProcessComponent implements OnInit {
  trace: any = null;
  objectKeys = Object.keys;
  isAdvanced: boolean = false;

  constructor(
    private simplifyService: SimplifyService,
    private settingsService: SettingsService
  ) {}

  ngOnInit(): void {
    this.simplifyService.trace$.subscribe(trace => {
      this.trace = trace;
    });

    this.settingsService.advancedMode$.subscribe(mode => {
      this.isAdvanced = mode === 'advanced';
    });
  }
}