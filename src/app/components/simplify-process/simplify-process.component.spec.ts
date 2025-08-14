// simplify-process.component.spec.ts

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SimplifyProcessComponent } from './simplify-process.component';
import { SimplifyService } from '../../services/simplify.service';
import { SettingsService } from '../../services/settings.service';
import { of } from 'rxjs';

describe('SimplifyProcessComponent', () => {
  let component: SimplifyProcessComponent;
  let fixture: ComponentFixture<SimplifyProcessComponent>;

  const mockTrace = {
    sections: '3 sections',
    cleaned: 'Cleaned text here.',
    keywords: {
      Intro: ['AI', 'learning'],
      Body: ['model', 'data']
    },
    chunks: 'Chunked data.'
  };

  const mockSimplifyService = {
    trace$: of(mockTrace)
  };

  const mockSettingsService = {
    advancedMode$: of('advanced')
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [SimplifyProcessComponent],
      providers: [
        { provide: SimplifyService, useValue: mockSimplifyService },
        { provide: SettingsService, useValue: mockSettingsService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(SimplifyProcessComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should show the simplification steps card when trace and isAdvanced are true', () => {
    const card = fixture.nativeElement.querySelector('.card');
    expect(card).toBeTruthy();
  });

  it('should not show the card if trace is missing', () => {
    component.trace = null;
    fixture.detectChanges();
    const card = fixture.nativeElement.querySelector('.card');
    expect(card).toBeFalsy();
  });

  it('should not show the card if isAdvanced is false', () => {
    component.isAdvanced = false;
    fixture.detectChanges();
    const card = fixture.nativeElement.querySelector('.card');
    expect(card).toBeFalsy();
  });

  it('should display keywords for each section', () => {
    const keywordItems = fixture.nativeElement.querySelectorAll('li ul li');
    expect(keywordItems.length).toBe(2); 
    expect(keywordItems[0].textContent).toContain('Intro');
    expect(keywordItems[1].textContent).toContain('Body');
  });
});
