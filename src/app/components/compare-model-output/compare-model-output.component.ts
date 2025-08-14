import { Component, OnInit } from '@angular/core';
import { SimplifyService } from '../../services/simplify.service';

@Component({
  selector: 'app-compare-model-output',
  standalone: false,
  templateUrl: './compare-model-output.component.html',
  styleUrl: './compare-model-output.component.css'
})
export class CompareModelOutputComponent implements OnInit {
  baselineText: string = '';

  constructor(private simplifyService: SimplifyService) {}

  ngOnInit(): void {
    this.simplifyService.baselineText$.subscribe(text => {
      this.baselineText = text;
    });
  }
}
