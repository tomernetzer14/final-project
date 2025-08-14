import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ApiService, SimplifyResponse } from './api.service';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ApiService]
    });

    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should send POST request to simplify endpoint with correct text', () => {
    const mockText = 'Simplify me, please!';
    const mockResponse: SimplifyResponse = {
      original: mockText,
      simplified: 'simplified version',
      keywords: { section: ['keyword'] },
      baseline: 'baseline text',
      trace: {},
      metrics: {
        readability: 90,
        complexity: 5,
        frequencyScore: 2,
        bert: 0.95,
        berts: 0.958
      }
    };

    service.simplifyText(mockText).subscribe(res => {
      expect(res).toEqual(mockResponse);
    });

    const req = httpMock.expectOne('http://localhost:5001/simplify');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ text: mockText });

    req.flush(mockResponse); 
  });
});
