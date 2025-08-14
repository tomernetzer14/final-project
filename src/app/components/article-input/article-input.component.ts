import { Component, ViewChild, ElementRef } from '@angular/core';
import { SimplifyService } from '../../services/simplify.service';
import { SettingsService } from '../../services/settings.service';
import { HttpClient } from '@angular/common/http';

import { ApiService, Metrics } from '../../services/api.service';
import Chart from 'chart.js/auto';
import * as pdfjsLib from 'pdfjs-dist';
(pdfjsLib as any).GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;


@Component({
  selector: 'app-article-input',
  standalone: false,
  templateUrl: './article-input.component.html',
  styleUrl: './article-input.component.css'
})
export class ArticleInputComponent {
  @ViewChild('fileInput') fileInput!: ElementRef;

  text: string = '';
  isFileUploaded: boolean = false;
  simplifySubscription: any;
  extractSub: any;

  constructor(
    private simplifyService: SimplifyService,
    private settingsService: SettingsService,
    private apiService: ApiService,
    private http: HttpClient
  ) {}

  onFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (!file) return;
  
    const fileType = file.name.split('.').pop()?.toLowerCase();
    this.isFileUploaded = true;
  
    if (fileType === 'pdf') {
      this.extractPdf(file);
    } 
    else if (fileType === 'txt') {
      this.extractTxt(file);
    } else {
      alert('Unsupported file type');
      this.onClear();
    }
  }  

  extractPdf(file: File) {
    this.extractSub = this.apiService.extractPdf(file).subscribe(xml => {
      this.text = this.parseTeiXml(xml);  
    }, err => {
      console.error('Error calling GROBID via backend:', err);
      this.text = "Error extracting PDF.";
    });
  }

  parseTeiXml(xmlStr: string): string {
    const parser = new DOMParser();
    const doc = parser.parseFromString(xmlStr, 'application/xml');
    const ns = 'http://www.tei-c.org/ns/1.0';
  
    const body = doc.getElementsByTagNameNS(ns, 'body')[0];
    if (!body) {
      console.warn('<body> not found on TEI');
      return '';
    }
  
    const divs = body.getElementsByTagNameNS(ns, 'div');
    const cleanedSections: string[] = [];
  
    for (let i = 0; i < divs.length; i++) {
      const div = divs[i];
      const divType = div.getAttribute('type')?.toLowerCase() || '';
  
      if (['references', 'bibliography', 'figure', 'table'].includes(divType)) {
        continue;
      }
  
      const heads = div.getElementsByTagNameNS(ns, 'head');
      const title = heads.length > 0 ? heads[0].textContent?.trim() : '';
  
      const ps = div.getElementsByTagNameNS(ns, 'p');
      const paragraphs: string[] = [];
  
      for (let j = 0; j < ps.length; j++) {
        const pText = ps[j].textContent?.trim().replace(/\s+/g, ' ') || '';
        if (pText.length > 0) {
          paragraphs.push(pText);
        }
      }
  
      if (paragraphs.length > 0) {
        let section = '';
        if (title) section += title + '\n';
        section += paragraphs.join('\n');
        cleanedSections.push(section);
      }
    }
  
    return cleanedSections.join('\n\n');
  }
  


  extractTxt(file: File) {
    const reader = new FileReader();
    reader.onload = (e: any) => {
      this.text = e.target.result;
    };
    reader.readAsText(file);
  }

  onSimplify() {
    const inputText = this.text.trim();
    if (!inputText) return;
  
    this.simplifyService.setSimplifiedText('Simplifying the text111');
    this.simplifyService.setBaselineText('');
    this.simplifyService.setBaselineText('');
    this.simplifyService.setTrace(null);
    this.simplifyService.setMetrics(null);
  
    this.simplifySubscription = this.apiService.simplifyText(inputText).subscribe({
      next: (res) => {
        this.simplifyService.setSimplifiedText(res.simplified);
        this.simplifyService.setKeywords(res.keywords);
        this.simplifyService.setBaselineText(res.baseline);
        this.simplifyService.setTrace(res.trace);
        this.simplifyService.setMetrics(res.metrics);

      },
      error: (err) => {
        console.error('שגיאה מהשרת:', err);
        this.simplifyService.setSimplifiedText('Error simplifying the text ❌');
      }
    });
  }

  onClear() {
  if (this.simplifySubscription) {
    this.simplifySubscription.unsubscribe();
    this.simplifySubscription = null;
  }
  if (this.extractSub){
    this.extractSub.unsubscribe();
    this.extractSub = null;
  }


  this.text = '';
  this.isFileUploaded = false;
  this.simplifyService.setMetrics(null);
  this.simplifyService.clear();

   if (this.fileInput) {
    this.fileInput.nativeElement.value = '';
  }
  }
  

  
}
