import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { ArticleInputComponent } from './article-input.component';
import { SimplifyService } from '../../services/simplify.service';
import { SettingsService } from '../../services/settings.service';
import { ApiService } from '../../services/api.service';
import { of, throwError } from 'rxjs';
import * as pdfjsLib from 'pdfjs-dist';
import { HttpClientTestingModule } from '@angular/common/http/testing';

describe('ArticleInputComponent', () => {
  let component: ArticleInputComponent;
  let fixture: ComponentFixture<ArticleInputComponent>;
  let mockSimplifyService: any;
  let mockApiService: any;

  beforeEach(async () => {
    mockSimplifyService = {
      setMetrics: jasmine.createSpy(),
      setSimplifiedText: jasmine.createSpy(),
      setKeywords: jasmine.createSpy(),
      setTrace: jasmine.createSpy(),
      setBaselineText: jasmine.createSpy(),
      clear: jasmine.createSpy()
    };

    mockApiService = {
      simplifyText: jasmine.createSpy()
    };

    await TestBed.configureTestingModule({
      declarations: [ArticleInputComponent],
      imports: [HttpClientTestingModule,FormsModule],
      providers: [
        { provide: SimplifyService, useValue: mockSimplifyService },
        { provide: SettingsService, useValue: {} },
        { provide: ApiService, useValue: mockApiService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ArticleInputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with empty text', () => {
    expect(component.text).toBe('');
  });

  it('should disable textarea if file is uploaded', async () => {
    component.isFileUploaded = true;
    fixture.detectChanges();
    await fixture.whenStable();
    const textarea: HTMLTextAreaElement = fixture.nativeElement.querySelector('#articleText');
    expect(textarea.disabled).toBeTrue();
  });

  it('should accept text input into textarea', async () => {
    component.text = 'Hello testing world!';
    fixture.detectChanges();
    await fixture.whenStable();
    const textarea: HTMLTextAreaElement = fixture.nativeElement.querySelector('#articleText');
    expect(textarea.value).toContain('Hello testing world!');
  });

  it('should show correct word count', () => {
    component.text = 'Angular is powerful';
    fixture.detectChanges();
    const wordCountElement: HTMLElement = fixture.nativeElement.querySelector('.text-muted');
    expect(wordCountElement.textContent).toContain('3 words');
  });

  it('should alert on unsupported file type', () => {
    spyOn(window, 'alert');
    const event = {
      target: {
        files: [new File([''], 'file.xyz')]
      }
    };
    component.onFileSelected(event);
    expect(window.alert).toHaveBeenCalledWith('Unsupported file type');
  });

  it('should trigger clear on unsupported file', () => {
    spyOn(component, 'onClear');
    const event = {
      target: {
        files: [new File([''], 'file.xyz')]
      }
    };
    component.onFileSelected(event);
    expect(component.onClear).toHaveBeenCalled();
  });

  it('should extract text from .txt file', () => {
    const mockText = 'This is a test file';
    const file = new File([mockText], 'sample.txt', { type: 'text/plain' });

    const fileReaderMock = {
      readAsText: jasmine.createSpy(),
      onload: () => {},
      result: mockText
    };

    spyOn(window as any, 'FileReader').and.returnValue(fileReaderMock);

    component.extractTxt(file);
    expect(fileReaderMock.readAsText).toHaveBeenCalledWith(file);
  });

  it('should call simplifyService methods on successful simplify', fakeAsync(() => {
    const dummyResponse = {
      simplified: 'Success message',
      keywords: ['important'],
      baseline: 'baseline text',
      trace: [],
      metrics: { score: 100 }
    };

    mockApiService.simplifyText.and.returnValue(of(dummyResponse));
    component.text = 'Some input text';
    component.onSimplify();
    tick();

    expect(mockSimplifyService.setSimplifiedText).toHaveBeenCalledWith('Simplifying the text111');
    expect(mockSimplifyService.setSimplifiedText).toHaveBeenCalledWith('Success message');    
    expect(mockSimplifyService.setKeywords).toHaveBeenCalledWith(dummyResponse.keywords);
    expect(mockSimplifyService.setBaselineText).toHaveBeenCalledWith(dummyResponse.baseline);
    expect(mockSimplifyService.setTrace).toHaveBeenCalledWith(dummyResponse.trace);
    expect(mockSimplifyService.setMetrics).toHaveBeenCalledWith(dummyResponse.metrics);
  }));

  it('should handle simplify API error', fakeAsync(() => {
    mockApiService.simplifyText.and.returnValue(throwError(() => new Error('API Error')));
    component.text = 'Some input text';
    component.onSimplify();
    tick();

    expect(mockSimplifyService.setSimplifiedText).toHaveBeenCalledWith('Error simplifying the text ❌');
  }));

  it('should clear text and unsubscribe on clear', () => {
    const mockSub = { unsubscribe: jasmine.createSpy() };
    component.simplifySubscription = mockSub as any;
    component.text = 'some text';

    component.onClear();

    expect(mockSub.unsubscribe).toHaveBeenCalled();
    expect(component.text).toBe('');
    expect(component.simplifySubscription).toBeNull();
  });


  it('should parse TEI XML and extract cleaned sections from PDF', () => {
    const teiXml = `
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
      <text>
        <body>
          <div type="section">
            <head>Introduction</head>
            <p>This is the introduction paragraph.</p>
          </div>
          <div type="references">
            <head>References</head>
            <p>This should be skipped.</p>
          </div>
        </body>
      </text>
    </TEI>`;
  
    mockApiService.extractPdf = jasmine.createSpy().and.returnValue(of(teiXml));
    const file = new File(['dummy'], 'sample.pdf', { type: 'application/pdf' });
  
    component.extractPdf(file);
  
    expect(component.text).toContain('Introduction');
    expect(component.text).toContain('This is the introduction paragraph.');
    expect(component.text).not.toContain('References');
  });
});
