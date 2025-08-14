import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ArticleOutputComponent } from './article-output.component';
import { SimplifyService } from '../../services/simplify.service';
import { of } from 'rxjs';
import { By } from '@angular/platform-browser';

describe('ArticleOutputComponent', () => {
  let component: ArticleOutputComponent;
  let fixture: ComponentFixture<ArticleOutputComponent>;

  const mockSimplifyService = {
    simplifiedText$: of('My simplified text'),
    keywords$: of({ 'Full Text': ['simplified'] })
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ArticleOutputComponent],
      providers: [{ provide: SimplifyService, useValue: mockSimplifyService }]
    }).compileComponents();

    fixture = TestBed.createComponent(ArticleOutputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should display simplified text', () => {
    const cardText = fixture.nativeElement.querySelector('.card-text');
    expect(cardText.innerHTML).toContain('simplified');
  });

  it('should highlight keywords in simplified text', () => {
    component.simplifiedText = 'this is a keyword';
    component.keywords = { 'Full Text': ['keyword'] };
    const html = component.highlightKeywords();
    expect(html).toContain('<span class="highlight" title="Keyword">keyword</span>');
  });

  it('should show gif if text includes "Simplifying the text111"', () => {
    component.simplifiedText = 'Simplifying the text111';
    fixture.detectChanges();
    const gif = fixture.nativeElement.querySelector('.loading-gif');
    expect(gif).toBeTruthy();
  });

  it('should show word count correctly', () => {
    component.simplifiedText = 'This is simplified example text';
    fixture.detectChanges();
    const countElement = fixture.nativeElement.querySelector('.text-muted');
    expect(countElement.textContent).toContain('5 words');
  });
});
