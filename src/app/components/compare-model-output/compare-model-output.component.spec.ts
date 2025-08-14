// compare-model-output.component.spec.ts

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CompareModelOutputComponent } from './compare-model-output.component';
import { SimplifyService } from '../../services/simplify.service';
import { of } from 'rxjs';

describe('CompareModelOutputComponent', () => {
  let component: CompareModelOutputComponent;
  let fixture: ComponentFixture<CompareModelOutputComponent>;

  const mockSimplifyService = {
    baselineText$: of('This is the baseline output of the model.')
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CompareModelOutputComponent],
      providers: [{ provide: SimplifyService, useValue: mockSimplifyService }]
    }).compileComponents();

    fixture = TestBed.createComponent(CompareModelOutputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should display the baseline text', () => {
    const textElement = fixture.nativeElement.querySelector('.card-text');
    expect(textElement.textContent).toContain('baseline output');
  });

  it('should show correct word count', () => {
    const wordCount = fixture.nativeElement.querySelector('.text-muted');
    expect(wordCount.textContent).toContain('8 words');
  });

  it('should not display card if baselineText is empty', () => {
    component.baselineText = '';
    fixture.detectChanges();
    const card = fixture.nativeElement.querySelector('.card');
    expect(card).toBeNull();
  });
});
