// metrics-output.component.spec.ts

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MetricsOutputComponent } from './metrics-output.component';
import { SimplifyService } from '../../services/simplify.service';
import { SettingsService } from '../../services/settings.service';
import { of } from 'rxjs';
import { Metrics } from '../../services/api.service';

describe('MetricsOutputComponent', () => {
  let component: MetricsOutputComponent;
  let fixture: ComponentFixture<MetricsOutputComponent>;

  const mockMetrics: Metrics = {
    readability: 70,
    complexity: 30,
    frequencyScore: 50,
    bert: 0.8,
    berts: 0.9
  };

  const mockSimplifyService = {
    metrics$: of(mockMetrics)
  };

  const mockSettingsService = {
    advancedMode$: of('advanced'),
    getCurrentMode: () => 'advanced'
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MetricsOutputComponent],
      providers: [
        { provide: SimplifyService, useValue: mockSimplifyService },
        { provide: SettingsService, useValue: mockSettingsService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MetricsOutputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should show the chart container when in advanced mode and metrics exist', () => {
    component.metrics = mockMetrics;
    component['settingsService'] = {
      getCurrentMode: () => 'advanced'
    } as any;
    fixture.detectChanges(); // <-- חובה!
    const chartCard = fixture.nativeElement.querySelector('.card');
    expect(chartCard).toBeTruthy();
  });
  it('should return true from shouldShowMetrics() in advanced mode with metrics', () => {
    component.metrics = mockMetrics;
    component['settingsService'] = {
      getCurrentMode: () => 'advanced'
    } as any;
    expect(component.shouldShowMetrics()).toBeTrue();
  });

  it('should return false from shouldShowMetrics() when no metrics available', () => {
    component.metrics = null;
    expect(component.shouldShowMetrics()).toBeFalse();
  });

  it('should return false from shouldShowMetrics() when not in advanced mode', () => {
    component.metrics = mockMetrics;
    component['settingsService'].getCurrentMode = () => 'basic';
    expect(component.shouldShowMetrics()).toBeFalse();
  });
});
